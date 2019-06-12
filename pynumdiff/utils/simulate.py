import numpy as _np
from scipy.integrate import odeint

# local imports
from pynumdiff.utils import utility as _utility
from pynumdiff.utils import __pi_cruise_control__ as __pi_cruise_control__
_finite_difference = _utility.finite_difference

def __add_noise__(x, noise_type, noise_parameters, random_seed):
    _np.random.seed(random_seed)
    timeseries_length = _np.max(x.shape)
    noise = _np.random.__getattribute__(noise_type)(noise_parameters[0], noise_parameters[1], timeseries_length)
    return x + noise

def sine(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):

    # Parameters
    ############
    f1 = 1
    f2 = 1.7
    y_offset = 1

    t = _np.arange(0, timeseries_length, simdt)
    x = (0.5*_np.sin(t*2*_np.pi*f1) + 0.5*_np.sin(t*2*_np.pi*f2)) + y_offset
    dxdt = 0.5*_np.cos(t*2*_np.pi*f1)*2*_np.pi*f1 + 0.5*_np.cos(t*2*_np.pi*f2)*2*_np.pi*f2
    #actual_vals = _finite_difference(_np.matrix(x), params=None, dt=dt)
    actual_vals = _np.matrix(_np.vstack((x, dxdt)))


    noisy_x = __add_noise__(x, noise_type, noise_parameters, random_seed)

    noisy_measurements = _np.matrix(noisy_x)
    extra_measurements = _np.matrix([])

    noisy_pos = _np.ravel(noisy_measurements)
    pos = _np.ravel(actual_vals[0,:])
    vel = _np.ravel(actual_vals[1,:])
    extras = None

    idx = _np.arange(0, len(t), int(dt/simdt))
    return noisy_pos[idx], pos[idx], vel[idx], None 

def triangle(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):
    t = _np.arange(0, timeseries_length, simdt)
    continuous_x = _np.sin(t*t)

    # find peaks and valleys
    peaks, valleys = _utility.peakdet(continuous_x, 0.1)

    # organize peaks and valleys
    if len(peaks) > 0:
        reversal_idxs = peaks[:,0].astype(int).tolist()
        reversal_idxs.extend(valleys[:, 0].astype(int).tolist())
        reversal_idxs.extend([0, len(continuous_x)-1])

        reversal_vals = peaks[:,1].tolist()
        reversal_vals.extend(valleys[:, 1].tolist())
        reversal_vals.extend([0, continuous_x[-1]])
    else:
        reversal_idxs = [0, len(continuous_x)-1]
        reversal_vals = [0, continuous_x[-1]]

    idx = _np.argsort(reversal_idxs)
    reversal_idxs = _np.array(reversal_idxs)[idx]
    reversal_vals = _np.array(reversal_vals)[idx]
    reversal_ts = t[reversal_idxs]

    x = _np.interp(t, reversal_ts, reversal_vals)
    smooth_x, dxdt = _finite_difference(x, dt=simdt)

    noisy_x = __add_noise__(x, noise_type, noise_parameters, random_seed)

    actual_vals = _np.matrix(_np.vstack((x, dxdt)))
    noisy_measurements = _np.matrix(noisy_x)
    extra_measurements = _np.matrix([])

    noisy_pos = _np.ravel(noisy_measurements)
    pos = _np.ravel(actual_vals[0,:])
    vel = _np.ravel(actual_vals[1,:])
    extras = None

    idx = _np.arange(0, len(t), int(dt/simdt))
    return noisy_pos[idx], pos[idx], vel[idx], None 

def pop_dyn(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):
    # http://www.biologydiscussion.com/population/population-growth/population-growth-curves-ecology/51854

    t = _np.arange(0, timeseries_length, simdt)
    K = 2 # carrying capacity
    r = 4 # biotic potential

    x = [0.1] # population
    dxdt = [r*x[-1]*(1-x[-1]/K)]
    for _t_ in t[1:]:
        x.append(x[-1] + simdt*dxdt[-1])
        dxdt.append(r*x[-1]*(1-x[-1]/K)) 

    x = _np.matrix(x)
    dxdt = _np.matrix(dxdt)

    noisy_x = __add_noise__(x, noise_type, noise_parameters, random_seed)

    actual_vals = _np.matrix(_np.vstack((x, dxdt)))
    noisy_measurements = _np.matrix(noisy_x)
    extra_measurements = _np.matrix([])

    noisy_pos = _np.ravel(noisy_measurements)
    pos = _np.ravel(actual_vals[0,:])
    vel = _np.ravel(actual_vals[1,:])
    extras = None

    idx = _np.arange(0, len(t), int(dt/simdt))
    return noisy_pos[idx], pos[idx], vel[idx], None 

def linear_autonomous(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):
    t = _np.arange(0, timeseries_length, simdt)

    A = _np.matrix([[1, simdt, 0], [0, 1, simdt], [-100, -3, 0.01]])
    print(A)
    x0 = _np.matrix([[0], [2], [0]])
    xs = x0
    for i in t:
        x = A*xs[:,-1]
        xs = _np.hstack((xs, x))

    x = xs[0,:]
    x *= 2

    smooth_x, dxdt = _finite_difference( _np.ravel(x), simdt)

    noisy_x = __add_noise__(x, noise_type, noise_parameters, random_seed)

    extras = None

    idx = _np.arange(0, len(t), int(dt/simdt))
    return _np.ravel(noisy_x)[1:][idx], smooth_x[1:][idx], dxdt[1:][idx], None 

def pi_control(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):
    t = _np.arange(0, timeseries_length, simdt)

    actual_vals, extra_measurements, controls = __pi_cruise_control__.run(timeseries_length, simdt)
    x = actual_vals[0,:]
    dxdt = actual_vals[1,:]

    noisy_x = __add_noise__(x, noise_type, noise_parameters, random_seed)

    actual_vals = _np.matrix(_np.vstack((x, dxdt)))
    noisy_measurements = _np.matrix(noisy_x)

    noisy_pos = _np.ravel(noisy_measurements)
    pos = _np.ravel(actual_vals[0,:])
    vel = _np.ravel(actual_vals[1,:])
    extras = None

    idx = _np.arange(0, len(t), int(dt/simdt))
    return noisy_pos[idx], pos[idx], vel[idx], _np.array(extra_measurements)[0,idx], _np.array(controls)[0,idx] 

def lorenz_x(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):
    noisy_measurements, actual_vals = lorenz_xyz(timeseries_length, noise_type, noise_parameters, random_seed, dt, simdt)

    noisy_pos = _np.ravel(noisy_measurements[0,:])
    pos = _np.ravel(actual_vals[0,:])
    vel = _np.ravel(actual_vals[3,:])

    return noisy_pos[idx], pos[idx], vel[idx], None

def lorenz_xyz(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):
    t = _np.arange(0, timeseries_length, simdt)

    sigma = 10
    beta = 8/3
    rho = 45

    x = 5
    y = 1
    z = 3
    xyz = _np.matrix([[x], [y], [z]])
    xyz_dot = None

    for _t_ in t:
        x, y, z = _np.ravel(xyz[:,-1])

        xdot = sigma*(y-x)
        ydot = x*(rho-z)-y
        zdot = x*y - beta*z

        new_xyz_dot = _np.matrix([[xdot], [ydot], [zdot]])
        if xyz_dot is None:
            xyz_dot = new_xyz_dot
        else:
            xyz_dot = _np.hstack((xyz_dot, new_xyz_dot))

        new_xyz = xyz[:,-1] + simdt*new_xyz_dot
        xyz = _np.hstack((xyz, new_xyz))

    x = xyz[0,0:-1] / 20.
    dxdt = xyz_dot[0,:] / 20.

    y = xyz[1,0:-1] / 20.
    dydt = xyz_dot[1,:] / 20.

    z = xyz[2,0:-1] / 20.
    dzdt = xyz_dot[2,:] / 20.

    noisy_x = __add_noise__(x, noise_type, noise_parameters, random_seed)
    noisy_y = __add_noise__(y, noise_type, noise_parameters, random_seed+1)
    noisy_z = __add_noise__(z, noise_type, noise_parameters, random_seed+2)

    actual_vals = _np.array(_np.vstack((x, y, z, dxdt, dydt, dzdt)))
    noisy_measurements = _np.array(_np.vstack((noisy_x, noisy_y, noisy_z)))
    extra_measurements = _np.array([])

    idx = _np.arange(0, len(t), int(dt/simdt))
    return noisy_measurements[:, idx], actual_vals[:, idx], None

def rk4_lorenz_xyz(timeseries_length=4, noise_type='normal', noise_parameters=[0, 0.5], random_seed=1, dt=0.01, simdt=0.0001):
    t = _np.arange(0, timeseries_length, simdt)

    sigma = 10
    beta = 8/3
    rho = 45

    def dxyz_dt(xyz, t):
        x,y,z = xyz
        xdot = sigma*(y-x)
        ydot = x*(rho-z)-y
        zdot = x*y - beta*z
        return [xdot, ydot, zdot]
        
        
    ts = _np.linspace(0, timeseries_length, timeseries_length/dt)
    xyz_0 = [5,1,3]
    #xyz_0 = [3, 7, 1]

    vals, extra = odeint(dxyz_dt, xyz_0, ts, full_output=True)
    vals = vals.T
    x = vals[0,:]/20.
    y = vals[1,:]/20.
    z = vals[2,:]/20.

    noisy_x = __add_noise__(x, noise_type, noise_parameters, random_seed)
    noisy_y = __add_noise__(y, noise_type, noise_parameters, random_seed+1)
    noisy_z = __add_noise__(z, noise_type, noise_parameters, random_seed+2)

    _, dxdt = _finite_difference(x, dt)
    _, dydt = _finite_difference(y, dt)
    _, dzdt = _finite_difference(z, dt)

    actual_vals = _np.array(_np.vstack((x, y, z, dxdt, dydt, dzdt)))
    noisy_measurements = _np.array(_np.vstack((noisy_x, noisy_y, noisy_z)))
    extra_measurements = _np.array([])

    #idx = _np.arange(0, len(t), int(dt/simdt))
    return noisy_measurements, actual_vals, None