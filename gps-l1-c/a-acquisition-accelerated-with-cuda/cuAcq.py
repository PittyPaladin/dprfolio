import numpy as np
import cupy as cp
import matplotlib.pyplot as plt
import scipy.signal
import cupyx.scipy

from utils import *

import sys
sys.path.append("../GNSS-DSP-tools")
import gnsstools.gps.ca as ca
import gnsstools.io as io

NT = 1024
nco_table_gpu = cp.exp(2 * cp.pi * 1j * cp.arange(NT) / NT)

def nco_gpu_matrix_lut(f, p, n):
    idx = p + f*cp.arange(n)[:, None]
    idx = cp.floor(idx * NT).astype(cp.int32)
    idx = cp.mod(idx, NT)
    return nco_table_gpu[idx]

def resample(x):
    fsr = 4096000.0/fs
    h = scipy.signal.firwin(161,1.5e6/(fs/2),window='hann')
    x = scipy.signal.filtfilt(h,[1],x)
    xr = np.interp((1/fsr)*np.arange(ms_pad*4096),np.arange(len(x)),np.real(x))
    xi = np.interp((1/fsr)*np.arange(ms_pad*4096),np.arange(len(x)),np.imag(x))
    x = xr+(1j)*xi
    return x

def nco_mix_signal(x_gpu, nco_lut):
    x_gpu = x_gpu.reshape(ms, n1ms)
    sig_mixed_t = x_gpu[:, None, :] * nco_lut[None, :, :]
    sig_mixed_f = cp.conj(cp.fft.fft(sig_mixed_t, axis=2))
    return sig_mixed_f

def get_ca_codes(prns, n):
    c_gpu = cp.empty((len(prns), n), 'complex64')
    incr = float(ca.code_length) / n
    for i, prn in enumerate(prns):
        ca_code = cp.asarray( ca.code(prn, 0, 0, incr, n).astype('float32') )
        c_gpu[i,:] = cp.fft.fft(ca_code)
    return c_gpu

#
# Acquisition search
#
def search(sig_mixed_f, ca_code_f):
    # Correlate with PRN code
    corr_f = ca_code_f * sig_mixed_f
    corr_t = cp.fft.ifft(corr_f, axis=2)
    corr_abs = cp.absolute(corr_t).sum(axis=0)

    # Get sample and doppler index of max value
    flat_idx = cp.argmax(corr_abs)
    n_cols = corr_abs.shape[1]
    s_idx = flat_idx % n_cols
    metrics = corr_abs[:, s_idx] / cp.mean(corr_abs, axis=1)
    d_idx = cp.argmax(metrics)

    m_metric = metrics[d_idx]
    m_code = CA_CODE_LEN * (s_idx / n1ms)
    m_doppler = dopplers[d_idx]

    return m_metric,m_code,m_doppler

if __name__ == "__main__":
    # ------------------------ Settings ------------------------
    filename = "resources/GPS-L1-2022-03-27.cs8"
    fs = 4_000_000 # Msps
    prns = [2, 11, 31]
    prns = np.arange(1,33)
    doppler_min = -7000.0
    doppler_max = 7000.0
    doppler_incr = 200.0
    ms = cp.int32(80) # ms of non-coherent integration
    # ----------------------------------------------------------

    # ----------------------- Constants ------------------------
    # CA code length
    CA_CODE_LEN = cp.int32(ca.code_length)
    # Canonical sample frequency with which acquisition is run, in Msps
    fs_acq = cp.int32(4_096_000)
    # Number of samples in 1 full PRN code, which takes 1 ms
    n1ms = fs_acq // 1000
    # ----------------------------------------------------------

    # -------------------- Precompute once ---------------------
    # NCO look-up table
    dopplers = cp.arange(doppler_min, doppler_max, doppler_incr)
    nco_lut = nco_gpu_matrix_lut(-dopplers/fs_acq, 0, n1ms).T.astype('complex64') # (n, dopplers)

    # C/A codes for all PRNs, in frequency domain
    ca_codes_f = get_ca_codes(prns, n1ms)
    # ----------------------------------------------------------


    # -------------------- Start acquisiton --------------------
    # [1] Read first portion of file
    ms_pad = ms + 5
    n = int(fs*0.001*ms_pad)
    fp = open(filename, "rb")
    x = io.get_samples_complex(fp,n)

    # [2] Resample to canonical sample rate that is power of 2
    cp.cuda.nvtx.RangePush(f"Resample")
    x = resample(x) # in CPU
    cp.cuda.nvtx.RangePop()

    cp.cuda.nvtx.RangePush(f"Samples2GPU")
    x_gpu = cp.asarray(x[:n1ms*ms], 'complex64') # move samples to GPU
    cp.cuda.nvtx.RangePop()

    # [3] Signal NCO mixing with all dopplers, in frequency domain
    cp.cuda.nvtx.RangePush(f"Mixer->LoadModule")
    sig_mixed_f = nco_mix_signal(x_gpu, nco_lut) # dummy to load
    cp.cuda.nvtx.RangePop()
    cp.cuda.nvtx.RangePush(f"Mixer")
    sig_mixed_f = nco_mix_signal(x_gpu, nco_lut)
    cp.cuda.nvtx.RangePop()

    # [4] Run parallel acquisition for each PRN
    results = {prn: None for prn in prns}

    for i, prn in enumerate(prns):
        cp.cuda.nvtx.RangePush(f"Search PRN: {prn}")
        metric, code, doppler = search(sig_mixed_f, ca_codes_f[i])
        cp.cuda.nvtx.RangePop()
        results[prn] = {
            "metric" : metric,
            "code" : code,
            "doppler" : doppler
        }

    # Display results
    for prn, result in results.items():
        print(f"prn {prn:3d} doppler {result['doppler']:7.1f} metric {result['metric']:5.2f} code_offset {result['code']:6.1f}")


