import time
import json
import logging
import csv

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd

from src.interface.sdl.sdl import get_sdl_manager, get_next_obs
from src.utils.config import get_config


logger = logging.getLogger(__name__)


class NsOranEnv(gym.Env):
    """
    Ns-O-RAN Environment that follows gym interface
    
    The env 
    
    """
    def __init__(self, ue_id: str):
        super(NsOranEnv, self).__init__()

        config = get_config()

        self.num_bs = config.ENV.NUM_BS
        self.num_ue = config.ENV.NUM_UE
        self.ue_id = ue_id

        namespace = config.SDL.NAMESPACE
        sdl_manager = get_sdl_manager()
        self.SDL = sdl_manager(namespace=namespace)

        self.action_space = spaces.Discrete(self.num_bs+1)
        self.observation_space = spaces.Box(low=-np.inf, high=+np.inf, shape=((self.num_bs*7)+4,), dtype=np.float32)
        
        self.state = None
        self.time_stamp = 0 
        self.episode = 0

        # To Save
        self.throughputs = [0]
        self.rewards = []
        self.actions = []
        self.hondovers = [0] # time to store HO
        self.costs = [0]

        # Variable to calculate the cost
        self.initial_cost = 1
        self.decay_constant = 0.1

    def reset(self, seed=None) -> np.ndarray:
        """Reset the state of the environment to an initial state"""
        try:
            du_obs, cuup, cucp = get_next_obs(self.SDL, self.ue_id)
            self._prepare_state(du_obs, cuup, cucp) 
            self.episode = 0
            return self.state.to_numpy(dtype=np.float32).reshape(self.observation_space.shape), {}
        except:
            return np.random.randint(-1, 1, size=(self.observation_space.shape)).astype(np.float32), {}

    def step(self, action: int):
        """
        The agent takes a step in the environment
            return (obs, reward, terminated, truncated, info.)
        """
        assert self.action_space.contains(action), "Invalid Action"
        self.episode += 1

        # Send E2 control via RC xApp if needed.
        self.actions.append(action)
        wrong_action = False
        if action != 0:
            # Send RC request for index +1
            wrong_action = self._check_action(action)
            if not wrong_action:
                logger.info(f"Send HO request for UE {self.ue_id}, to cell {action+1}")
                # TODO: Handle RC request here
                # self.rc_agent.send_rc_request(ueid=self.ue_id, target_cell=action+1)
                self.hondovers.append(self.time_stamp)
            
        try:
            du_obs, cuup, cucp = get_next_obs(self.SDL, self.ue_id)
        except:
            return self.state.to_numpy(dtype=np.float32).reshape(self.observation_space.shape), 0, True, False, {}

        self._prepare_state(du_obs, cuup, cucp)
        reward = -20 if wrong_action else self._calculate_reward()

        terminated = False
        if self.episode % 10 == 0:
            self.save()
            terminated = True
        return self.state.to_numpy(dtype=np.float32).reshape(self.observation_space.shape), reward, terminated, False, {}

    def _prepare_state(self, du_obs: list[str], cuup: list[str], cucp: list[str]) -> None:
        columns = [ 
            'numActiveUes_cell2', "sinr_cell2", "dlPrbUsage_cell2", "TB.TotNbrDlInitial_cell2", "TB.TotNbrDlInitial.Qpsk_cell2", "TB.TotNbrDlInitial.64Qam_cell2", "TB.TotNbrDlInitial.16Qam_cell2",
            'numActiveUes_cell3', "sinr_cell3", "dlPrbUsage_cell3", "TB.TotNbrDlInitial_cell3", "TB.TotNbrDlInitial.Qpsk_cell3", "TB.TotNbrDlInitial.64Qam_cell3", "TB.TotNbrDlInitial.16Qam_cell3",
            'numActiveUes_cell4', "sinr_cell4", "dlPrbUsage_cell4", "TB.TotNbrDlInitial_cell4", "TB.TotNbrDlInitial.Qpsk_cell4", "TB.TotNbrDlInitial.64Qam_cell4", "TB.TotNbrDlInitial.16Qam_cell4",
            'numActiveUes_cell5', "sinr_cell5", "dlPrbUsage_cell5", "TB.TotNbrDlInitial_cell5", "TB.TotNbrDlInitial.Qpsk_cell5", "TB.TotNbrDlInitial.64Qam_cell5", "TB.TotNbrDlInitial.16Qam_cell5",
            "ueImsiComplete", "PSCell", "sinr_PSCell", "cost", "QosFlow.PdcpPduVolumeDL_Filter.UEID(txPdcpPduBytesNrRlc)"
        ]
        self.state = pd.DataFrame(0, index=range(1), columns=columns)
        self.state["ueImsiComplete"] = self.ue_id

        self._prepare_du(du_obs)
        self._prepare_cuup(cuup)
        self._prepare_cucp(cucp)

        self.state = self.state.drop(columns=["ueImsiComplete"])

    def _prepare_du(self, du: list[str]) -> None:
        columns = [ 
            "timestamp", "ueImsiComplete", "plmId", "nrCellId", "dlAvailablePrbs", "ulAvailablePrbs", "qci", "dlPrbUsage", 
            "ulPrbUsage", "TB.TotNbrDl.1", "TB.TotNbrDlInitial", "TB.TotNbrDlInitial.Qpsk", "TB.TotNbrDlInitial.16Qam", 
            "TB.TotNbrDlInitial.64Qam", "RRU.PrbUsedDl", "TB.ErrTotalNbrDl.1", "QosFlow.PdcpPduVolumeDL_Filter", 
            "CARR.PDSCHMCSDist.Bin1", "CARR.PDSCHMCSDist.Bin2", "CARR.PDSCHMCSDist.Bin3", "CARR.PDSCHMCSDist.Bin4", 
            "CARR.PDSCHMCSDist.Bin5", "CARR.PDSCHMCSDist.Bin6", "L1M.RS-SINR.Bin34", "L1M.RS-SINR.Bin46", "L1M.RS-SINR.Bin58",
            "L1M.RS-SINR.Bin70", "L1M.RS-SINR.Bin82", "L1M.RS-SINR.Bin94", "L1M.RS-SINR.Bin127", "DRB.BufferSize.Qos", 
            "DRB.MeanActiveUeDl", "TB.TotNbrDl.1.UEID", "TB.TotNbrDlInitial.UEID", "TB.TotNbrDlInitial.Qpsk.UEID", 
            "TB.TotNbrDlInitial.16Qam.UEID", "TB.TotNbrDlInitial.64Qam.UEID", "TB.ErrTotalNbrDl.1.UEID", 
            "QosFlow.PdcpPduVolumeDL_Filter.UEID", "RRU.PrbUsedDl.UEID", "CARR.PDSCHMCSDist.Bin1.UEID", 
            "CARR.PDSCHMCSDist.Bin2.UEID", "CARR.PDSCHMCSDist.Bin3.UEID", "CARR.PDSCHMCSDist.Bin4.UEID", 
            "CARR.PDSCHMCSDist.Bin5.UEID", "CARR.PDSCHMCSDist.Bin6.UEID", "L1M.RS-SINR.Bin34.UEID", "L1M.RS-SINR.Bin46.UEID", 
            "L1M.RS-SINR.Bin58.UEID", "L1M.RS-SINR.Bin70.UEID", "L1M.RS-SINR.Bin82.UEID", "L1M.RS-SINR.Bin94.UEID", 
            "L1M.RS-SINR.Bin127.UEID", "DRB.BufferSize.Qos.UEID", "DRB.UEThpDl.UEID", "DRB.UEThpDlPdcpBased.UEID" 
        ]
        du = pd.DataFrame([du], columns=columns)
        du['ueImsiComplete'] = du['ueImsiComplete'].astype(int)
        ue_du = du.loc[(du["ueImsiComplete"] == self.ue_id)]
        if not ue_du.empty:
            self.time_stamp= int(ue_du['timestamp'].values[0])
            cellid = int(ue_du['nrCellId'].values[0]) 
            dlPrbUsages = float(ue_du['dlPrbUsage'].values[0])
            total = float(ue_du['TB.TotNbrDlInitial'].values[0])
            qpsk = float(ue_du['TB.TotNbrDlInitial.Qpsk'].values[0])
            qam16 = float(ue_du['TB.TotNbrDlInitial.16Qam'].values[0])
            qam64 = float(ue_du['TB.TotNbrDlInitial.64Qam'].values[0])


            self.state[f'dlPrbUsage_cell{cellid}'] =  dlPrbUsages
            if total == 0:
                self.state[f'TB.TotNbrDlInitial.Qpsk_cell{cellid}'] = 0
                self.state[f'TB.TotNbrDlInitial.16Qam_cell{cellid}'] = 0
                self.state[f'TB.TotNbrDlInitial.64Qam_cell{cellid}'] = 0
                self.state[f'TB.TotNbrDlInitial_cell{cellid}'] = 0
            else:
                self.state[f'TB.TotNbrDlInitial.Qpsk_cell{cellid}'] = qpsk / total
                self.state[f'TB.TotNbrDlInitial.16Qam_cell{cellid}'] = qam16 / total
                self.state[f'TB.TotNbrDlInitial.64Qam_cell{cellid}'] = qam64 / total
                self.state[f'TB.TotNbrDlInitial_cell{cellid}'] = total
    
    def _prepare_cuup(self, cuup: list[str]) -> None:
        columns = [ 
            "timestamp", "ueImsiComplete", "DRB.PdcpSduDelayDl (cellAverageLatency)", 
            "m_pDCPBytesUL (0)", "m_pDCPBytesDL (cellDlTxVolume)", "DRB.PdcpSduVolumeDl_Filter.UEID (txBytes)", 
            "Tot.PdcpSduNbrDl.UEID (txDlPackets)", "DRB.PdcpSduBitRateDl.UEID(pdcpThroughput)", "DRB.PdcpSduDelayDl.UEID (pdcpLatency)", 
            "QosFlow.PdcpPduVolumeDL_Filter.UEID(txPdcpPduBytesNrRlc)", "DRB.PdcpPduNbrDl.Qos.UEID (txPdcpPduNrRlc)" 
        ]
        cuup = pd.DataFrame([cuup], columns=columns)
        cuup['ueImsiComplete'] = cuup['ueImsiComplete'].astype(int)
        ue_cuup = cuup.loc[(cuup["ueImsiComplete"] == self.ue_id)]
        if not ue_cuup.empty:  
            throughput = ue_cuup['QosFlow.PdcpPduVolumeDL_Filter.UEID(txPdcpPduBytesNrRlc)'].values[0]
            self.throughputs.append(float(throughput))
            time_now = int(ue_cuup['timestamp'].iloc[0]) / 1000
            cost = self.initial_cost * np.exp(-self.decay_constant*(time_now-(self.hondovers[-1] / 1000)))
            self.state["cost"] = cost
            self.costs.append(cost)
        
    def _prepare_cucp(self, cucp: list[str]):
        columns = [ 
            "timestamp", "ueImsiComplete", "numActiveUes", "DRB.EstabSucc.5QI.UEID (numDrb)", "DRB.RelActNbr.5QI.UEID (0)", 
            "L3 serving Id(m_cellId)", "UE (imsi)", "L3 serving SINR", "L3 serving SINR 3gpp", "L3 neigh Id 1 (cellId)", 
            "L3 neigh SINR 1", "L3 neigh SINR 3gpp 1 (convertedSinr)", "L3 neigh Id 2 (cellId)", "L3 neigh SINR 2",
            "L3 neigh SINR 3gpp 2 (convertedSinr)", "L3 neigh Id 3 (cellId)", "L3 neigh SINR 3", "L3 neigh SINR 3gpp 3 (convertedSinr)", 
            "L3 neigh Id 4 (cellId)", "L3 neigh SINR 4", "L3 neigh SINR 3gpp 4 (convertedSinr)", "L3 neigh Id 5 (cellId)", 
            "L3 neigh SINR 5", "L3 neigh SINR 3gpp 5 (convertedSinr)", "L3 neigh Id 6 (cellId)", "L3 neigh SINR 6", 
            "L3 neigh SINR 3gpp 6 (convertedSinr)", "L3 neigh Id 7 (cellId)", "L3 neigh SINR 7", "L3 neigh SINR 3gpp 7 (convertedSinr)", 
            "L3 neigh Id 8 (cellId)", "L3 neigh SINR 8", "L3 neigh SINR 3gpp 8 (convertedSinr)" 
        ]
        cucp = pd.DataFrame([cucp], columns=columns)
        for cellid in ['2','3','4','5']:
            condition = (cucp['L3 serving Id(m_cellId)'] == cellid)
            n_ue = cucp.loc[condition]['numActiveUes'].to_numpy()
            # if there is no Ue connected to a cell
            if len(n_ue) == 0:
                n_ue = [0]
            self.state[f'numActiveUes_cell{cellid}'] = int(n_ue[0])
        cucp['ueImsiComplete'] = cucp['ueImsiComplete'].astype(int)
        ue_cucp = cucp.loc[(cucp["ueImsiComplete"] == self.ue_id)]
        if not ue_cucp.empty:
            serving_cell = int(ue_cucp['L3 serving Id(m_cellId)'].values[0])
            serving_sinr = float(ue_cucp['L3 serving SINR'].values[0])
            cell1 = int(ue_cucp['L3 neigh Id 1 (cellId)'].values[0])
            cell2 = int(ue_cucp['L3 neigh Id 2 (cellId)'].values[0])
            cell3 = int(ue_cucp['L3 neigh Id 3 (cellId)'].values[0])
            sinr1 = float(ue_cucp['L3 neigh SINR 1'].values[0])
            sinr2 = float(ue_cucp['L3 neigh SINR 2'].values[0])
            sinr3 = float(ue_cucp['L3 neigh SINR 3'].values[0])

            self.state[f'sinr_cell{serving_cell}'] =  serving_sinr
            self.state[f'sinr_cell{cell1}'] = sinr1
            self.state[f'sinr_cell{cell2}'] = sinr2
            self.state[f'sinr_cell{cell3}'] = sinr3
            self.state["PSCell"] =  serving_cell
            self.state["sinr_PSCell"] =  serving_sinr
        
    def _calculate_reward(self) -> float:
        before = 1.0 if len(self.throughputs) < 2 else self.throughputs[-2]
        before = 1.0 if before == 0 else before
        after = self.throughputs[-1]
        after = 1.0 if after == 0 else after
        improve_th = (np.log(after * 8 / 1000000) - np.log(before * 8 / 1000000))
        # If HO occurred!
        if self.actions[-1] != 0:
            reward = improve_th - self.costs[-2]
        else:
            reward = improve_th
        self.rewards.append(reward)
        return reward

    def _check_action(self, action: int) -> bool:
        serving_cell = int(self.state["PSCell"].values[0])
        if serving_cell == action + 1:
            logger.error(f"ue: {self.ue_id}, serving cell: {serving_cell}, target cell {action+1}")
            return True
        return False

    def save(self):
        """Close the environment:
        Store throughputs, rewards, actions, hondovers, costs
        """
        # Store logs and metrics
        with open(f"rewards{self.ue_id}.csv", mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.rewards)
        with open(f"actions{self.ue_id}.csv", mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.actions)
        with open(f"throughputs{self.ue_id}.csv", mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.throughputs)   
        logger.info(f"Saved for ue {self.ue_id}")