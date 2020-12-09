#!/usr/bin/env python


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ===============================================
# ============== The Ising Class ================
# ===============================================


class Ising:
    """ The ising platform that ising simulation happens """
    def __init__(self, L, beta):
        self.data = np.random.choice([-1, 1], size=(L, L))
        self.beta = beta
        self.size = L
        self.decision = np.exp(- beta * np.array([-8, -4, 0, 4, 8]))

    def reset(self, beta):
        """ reset the to random data for new temp. """
        # self.data = np.random.choice([-1, 1], size=(self.size, self.size))
        self.beta = beta
        self.decision = np.exp(- beta * np.array([-8, -4, 0, 4, 8]))

    def distro(self, x):
        """boltzman distribution of energy"""
        if x > 0:
            return np.exp(- self.beta * x)
        return np.power(10, -24)

    def decide(self, vert, horz):
        """metropolis decision with periodic boundary conditions"""
        # calculate delta E
        delta_e = 2 * self.data[vert][horz] * (
            self.data[vert - 1][horz] +
            self.data[(vert + 1) % self.size][horz] +
            self.data[vert][horz - 1] +
            self.data[vert][(horz + 1) % self.size]
            )

        # find the index of delta E for self.decision
        decision_index = (delta_e + 8) // 4

        # report for debugging
        # print("[info]:decide: ", delta_e,
        #       self.decision[decision_index], "\n")
        # decide
        return np.random.uniform(0, 1) < self.decision[decision_index]

    def metropolis(self):
        """ evolve using metropolis """
        # every cell has chance to flip (ammortized)
        for _ in range(self.size ** 2):
            vert = np.random.randint(0, self.size)
            horz = np.random.randint(0, self.size)
            if self.decide(vert, horz):
                self.data[vert][horz] *= -1

    def energy(self):
        """ calculate and return the energy of the ising model """
        energy = 0
        for vert in range(self.size):
            for horz in range(self.size):
                # sum of sigma_i and sigma_j in the neighborhood
                energy += -1 * self.data[vert][horz] * (
                    self.data[vert - 1][horz] +
                    self.data[(vert + 1) % self.size][horz] +
                    self.data[vert][horz - 1] +
                    self.data[vert][(horz + 1) % self.size]
                    )

        return energy / 2.0

    def equalize(self):
        """ evolve the system to equilibrium """
        # for _ in range(100):
        #     self.metropolis()
        en = []
        relaxed = False
        threshold = np.exp(-3)
        while not relaxed:
            # evolve 100 times
            for _ in range(100):
                self.metropolis()
                en.append(self.energy())

            # calculate auto_correlation for the j_th distance
            en_array = np.array(en)
            j = len(en_array) // 10
            auto_cor = (np.dot(en_array, np.roll(en_array, j)) / len(en_array)
                - np.mean(en_array) ** 2) / np.var(en_array)

            print("[Info]:equalize: auto_cor =", auto_cor)
            # if auto_cor is less than exp(-5), we have reached equilibrium
            if np.absolute(auto_cor) < threshold:
                relaxed = True
                print("[Info]:equalize: System Relaxed")

        return np.array(en)


    def magnetization(self):
        return np.absolute(np.sum(self.data) / self.size ** 2)


# =================================================
# ============= Auto Correlation Length ===========
# =================================================

def corr_len(array):
    """ take 1-D array and return auto-correlation length """
    n = len(array) // 10
    auto_cor = np.zeros(n)

    for j in range(n):
        # compute auto correlation for j
        auto_cor[j] = (np.dot(array, np.roll(array, j)) / len(array)
            - np.mean(array) ** 2) / np.var(array)

    # return the first j for which the auto_cor goes under exp(-1)
    return len(auto_cor[auto_cor > np.exp(-1)]) + 1

# ==================================================
# ================= data acquisition ===============
# ==================================================


def get_data(ising, step):
    """ take data about energies in the step length of cor_len """
    energies = np.zeros(100)
    mag = np.zeros(100)
    for i in range(100):
        for _ in range(step):
            ising.metropolis()

        energies[i] = ising.energy()
        mag[i] = ising.magnetization()

    return np.mean(energies), np.var(energies), np.mean(mag), np.var(mag)

# =================================================
# =================== Simulation ==================
# =================================================


def simulate(length, betas):
    """ simulate in various temp.s for ising model of length L """
    # Initialize the Ising System
    ising = Ising(50, 0.1)

    mean_energy_beta = np.zeros(40)
    var_energy_beta = np.zeros(40)
    mean_magnet_beta = np.zeros(40)
    var_magnet_beta = np.zeros(40)

    for index in range(len(betas)):
        ising.reset(betas[index])
        print("\n[Info]:main: beta =", betas[index])
        # equalie the system
        ising.equalize()

        # Find auto correlation length
        n = 100
        en = np.zeros(n)
        for i in range(n):
            ising.metropolis()
            en[i] = ising.energy()
        cor_len = corr_len(en)
        print("[Info]:main: corr_len =", cor_len)

        # get data
        mean_energy_beta[index], var_energy_beta[index], mean_magnet_beta[index], var_magnet_beta[index] = get_data(ising, 10)

    # calculate ksi and heat capacity
    ksi = betas * var_magnet_beta
    heat_capacity = betas ** 2 * var_energy_beta

    return mean_energy_beta, mean_magnet_beta, ksi, heat_capacity

# =================================================
# ==================== Main =======================
# =================================================


def main():
    """Main body"""
    # n = eval(input("[Input]:main: Enter the number of rounds: "))
    # beta = eval(input("[Input]:main: Enter beta: "))

    # make length range
    lengths = np.array([100, 110, 130, 160, 200])
    # make a linear space of beta
    betas = np.linspace(0.1, 0.7, 40)
    # initialize the data set
    energy = np.zeros(shape=(len(lengths), len(betas)))
    magnet = np.zeros(shape=(len(lengths), len(betas)))
    ksi = np.zeros(shape=(len(lengths), len(betas)))
    heat_cap = np.zeros(shape=(len(lengths), len(betas)))

    # choose length of the ising model
    for i in range(len(lengths)):
        # simulate
        print("[Info]:main: Ising size =", lengths[i])
        energy[i], magnet[i], ksi[i], heat_cap[i] = simulate(lengths[i], betas)

    # save data to CSV files
    df_energy = pd.DataFrame(energy)
    df_energy.to_csv("energy.csv")
    df_magnet = pd.DataFrame(magnet)
    df_magnet.to_csv("magnet.csv")
    df_ksi = pd.DataFrame(ksi)
    df_ksi.to_csv("ksi.csv")
    df_heat_cap = pd.DataFrame(heat_cap)
    df_heat_cap.to_csv("heat_cap.csv")

    # plot heat capacity
    for i in range(len(lengths)):
        plt.plot(betas, heat_cap, ls='-.', marker='^',
                 label="ising size =" + str(lengths[i]))
    plt.xlabel("beta")
    plt.ylabel("C_v")
    plt.tight_layout()
    plt.legend()
    plt.grid()
    plt.savefig("heat_cap_plot.jpg", bbox_inches='tight')
    plt.close()

    # plot ksi
    for i in range(len(lengths)):
        plt.plot(betas, ksi, ls='-.', marker='o',
                 label="ising size =" + str(lengths[i]))
    plt.xlabel("beta")
    plt.ylabel("ksi")
    plt.tight_layout()
    plt.legend()
    plt.grid()
    plt.savefig("ksi_plot.jpg", bbox_inches='tight')
    plt.close()

    # plot magnetization
    for i in range(len(lengths)):
        plt.plot(betas, magnet, ls='--', marker='o',
                 label="ising size =" + str(lengths[i]))
    plt.xlabel("beta")
    plt.ylabel("<M>")
    plt.tight_layout()
    plt.legend()
    plt.grid()
    plt.savefig("mag_plot.jpg", bbox_inches='tight')
    plt.close()

    # plot energy
    for i in range(len(lengths)):
        plt.plot(betas, energy, ls='--', marker='*',
                 label="ising size =" + str(lengths[i]))
    plt.xlabel("beta")
    plt.ylabel("<E>")
    plt.tight_layout()
    plt.legend()
    plt.grid()
    plt.savefig("energy_plot.jpg", bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    main()