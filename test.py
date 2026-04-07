import asyncio
import signal

class Programme:
    def __init__(self):
        self._reload_event = asyncio.Event()

    async def run(self):
        while True:
            # Vérifie si un reload est demandé
            if self._reload_event.is_set():
                self._reload_event.clear()
                await self.reload()

            # Ton travail principal
            await asyncio.sleep(1)

    async def reload(self):
        print("Reload demandé via SIGHUP")
        # ton code de reload ici

######################

def setup_signal_handlers(programme: Programme):
    loop = asyncio.get_running_loop()

    def on_sighup():
        # On déclenche l'événement dans la loop async
        programme._reload_event.set()

    loop.add_signal_handler(signal.SIGHUP, on_sighup)

##################

async def main():
    programme = Programme()
    setup_signal_handlers(programme)
    await programme.run()

if __name__ == "__main__":
    asyncio.run(main())