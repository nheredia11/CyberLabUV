"""Utilidades compartidas por las pruebas."""


class FakeDocker:
    """Sustituto de `_run_cmd_async`: registra las llamadas y responde como Docker.

    - `docker compose ... port <servicio> 5000` devuelve el puerto que Docker habría publicado.
    - Cualquier otro comando devuelve `exec_stdout`.
    """

    def __init__(self, exec_stdout="ok\n", port="127.0.0.1:49200\n", fail_up=False, fail_port=False):
        self.exec_stdout = exec_stdout
        self.port = port
        self.fail_up = fail_up
        self.fail_port = fail_port
        self.calls: list[list[str]] = []

    async def __call__(self, cmd, cwd, env=None, timeout=180):
        self.calls.append(list(cmd))
        if "up" in cmd and self.fail_up:
            return 1, "", "Bind for 127.0.0.1:8100 failed: port is already allocated"
        if "port" in cmd:
            return (1, "", "no port") if self.fail_port else (0, self.port, "")
        return 0, self.exec_stdout, ""

    def verbs(self):
        """Verbo de docker compose de cada llamada (up, port, down, exec...)."""
        found = []
        for call in self.calls:
            for verb in ("up", "port", "down", "exec"):
                if verb in call:
                    found.append(verb)
                    break
        return found
