async def main():
    async with lifespan() as adapters:
        telegram_adapter, vk_adapter, max_adapter = adapters
        try:
            await asyncio.gather(
                telegram_adapter.start(),
                vk_adapter.start(),
                max_adapter.start()
            )
        except KeyboardInterrupt:
            logger.info("shutdown_requested")
        except Exception as e:
            logger.error("fatal_error", error=str(e))
            raise