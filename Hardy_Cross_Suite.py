import re
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None  # default 'warn'

loop_name_list = pd.ExcelFile('Data/Hardy_Cross_input.xlsx').sheet_names

loops_from_input_file = []

for loop_name in loop_name_list:
    loops_from_input_file.append(pd.read_excel('Data/Hardy_Cross_input.xlsx', sheetname=loop_name))


class HardyCross(object):

    def __init__(self, loops):
        self.runs = 100
        self.threshold = 1
        self.loops = loops
        self.common_loops = []
        self.delta_Qs = np.zeros(len(self.loops))
        self.velocities = []
        self.new_D = []
        self.smallest_flow_rate = []
        self.max_velocity = 2.0
        self.min_velocity = 0.6

    def sort_edge_names_and_compute_pipe_diameters(self):

        for loop in self.loops:
            for i, Q in enumerate(loop['Q']):
                loop['D'][i] = diameter(loop['Q'][i])

        for i, loop in enumerate(self.loops):
            for j, section in enumerate(loop['Section']):
                loop['Section'][j] = add_string_from_list(*sorted(re.findall('[A-Z]', section)))

    def locate_common_loops(self):

        for loop in self.loops:
            self.common_loops.append(np.zeros((loop.shape[0], len(self.loops))))
        print(self.common_loops)

        # the for loops bellow create a sparse matrix were common loops are indicated
        for i, loop in enumerate(loops_from_input_file):
            for j in range(len(loops_from_input_file)):
                if i == j:
                    continue
                else:
                    for k, section1 in enumerate(self.loops[i]['Section']):
                        for l, section2 in enumerate(self.loops[j]['Section']):
                            if section1 == section2:
                                print('loop {} @location {}, loop {} @location {} '.format(i, k, j, l))
                                self.common_loops[i][k][j] = 1
        print(self.common_loops)

    def compute_velocities_of_each_loop(self):
        us = []
        for loop in self.loops:
            us.append(abs(velocity(loop['Q'], loop['D'])))
        return us

    def run_hc(self):
        for run in range(self.runs):
            for i, loop in enumerate(self.loops):
                loop['J'] = j_loss_10atm(loop['D'], loop['Q'])
                loop['hf'] = np.copysign(loop['J'] * loop['L'], loop['Q'])
                loop['hf/Q'] = loop['hf'] / loop['Q']
                self.delta_Qs[i] = (flow_correction_dq(loop['hf'], loop['hf/Q']))
                loop['Q'] = loop['Q'] + self.delta_Qs[i]
                self.delta_Qs[i] = (flow_correction_dq(loop['hf'], loop['hf/Q']))
                loop['Q'] = loop['Q'] - np.dot(self.common_loops[i], self.delta_Qs)
                self.smallest_flow_rate.append(np.min(np.abs(loop['Q'])))

            largest_dq_flow_rate = np.max(abs(self.delta_Qs))
            if largest_dq_flow_rate / np.min(self.smallest_flow_rate) * 100 < self.threshold:
                print('Completed on run {}'.format(run))
                print('dqmin / Qmin * 100 =  {0:.2f}'.format((largest_dq_flow_rate /
                                                              np.min(self.smallest_flow_rate)) * 100))
                for k, l in enumerate(loops_from_input_file):
                    print('the corrected loops {} are \n {}'.format(k, l))
                break
            else:
                print('Not Done {}'.format(run))
                pass
        return self.loops, self.delta_Qs

    def save_flows_to_file(self):
        with pd.ExcelWriter('Data/Hardy_Cross_network_flow_output.xlsx') as writer:
            for t, sheet in enumerate(loop_name_list):
                self.loops[t].to_excel(writer, sheet_name=sheet, index=None)


def add_string_from_list(*string_list):
    """
    :rtype : str

    """
    null = ''
    for string in string_list:
        null = null + string
    return null


def flow_correction_dq(df_hf, df_hf_q):
    """

    :type df_hf_q: float
    :type df_hf: float
    """
    return -(np.sum(df_hf) / (2 * np.sum(df_hf_q)))


def j_loss_10atm(d, q):

    """
    :param d: float
    :param q: float
    d: diameter [mm]
    q: flow rate [l/s]
    j: losses [m]
    """
    j_losses = (8.21 * 10 ** -4) * (((d * 10 ** -3) * 0.905) ** -4.76) * (np.abs(q * 10 ** -3) ** 1.76)
    return j_losses


def diameter_from_available(theoretical_diameter):
    available_diameters = [50., 63., 75., 90., 110., 125., 140., 160., 180., 200.,
                           225., 250., 280., 315., 355., 400.]
    for i, D in enumerate(available_diameters):
        if D < theoretical_diameter:
            pass
        else:
            theoretical_diameter = D
            break
    return theoretical_diameter


def diameter(q, velocity_for_diameter=0.8, show=0):
    """
    Q: flow rate [l/s]
    velocity_for_diameter: flow velocity m/s
    D: diameter [mm]
    """
    theoretical_diameter = np.sqrt((4 * np.abs(q) * 10 ** -3) / (np.pi * velocity_for_diameter)) * 10 ** 3
    if show:
        print('The Theoretical Diameter is {}'.format(theoretical_diameter))
    available_diameters = [50., 63., 75., 90., 110., 125., 140., 160., 180., 200., 225., 250., 280., 315., 355., 400.]
    for i, D in enumerate(available_diameters):
        if D < theoretical_diameter:
            pass
        else:
            theoretical_diameter = D
            break
    return theoretical_diameter


def velocity(q, d):
    numerator = 4. * (q*10**-3)
    denominator = ((d*10**-3) ** 2) * np.pi
    return numerator / denominator

if __name__ == '__main__':
    hc = HardyCross(loops_from_input_file)
    #hc.sort_edge_names_and_compute_pipe_diameters()
    hc.locate_common_loops()
    #hc.run_hc()
    #hc.save_flows_to_file()

    input("Press enter to quit.")
