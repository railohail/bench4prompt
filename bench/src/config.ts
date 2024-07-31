interface Config {
  apiUrl: string
  //   wsUrl: string
}

export const config: Config = {
  apiUrl: `http://${window.location.hostname}:8000`
  //   wsUrl: `ws://${window.location.hostname}:8000/ws`
}
