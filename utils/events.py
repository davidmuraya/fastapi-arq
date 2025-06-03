from database.models import configure


async def on_start_up() -> None:
    """
    Function to initialize the database.
    """
    configure()


async def on_shutdown() -> None:
    """
    Function to close the http client.
    """
    pass
