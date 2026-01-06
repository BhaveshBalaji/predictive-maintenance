import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000"
});

export const getMachines = async () =>
  (await api.get("/machines")).data;

export const getMachineMetrics = async (machineId: string) =>
  (await api.get(`/machines/${machineId}/metrics`)).data;

export const getActions = async () =>
  (await api.get("/actions")).data;

export const postMachineAction = async (machineId: string, action: string) =>
  (await api.post(`/machines/${machineId}/action?action=${action}`)).data;

export default api;
