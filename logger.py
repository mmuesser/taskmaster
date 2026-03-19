import logging


class Logger:
    def __init__(self):    
        self.logger = logging.getLogger("Taskmaster")
        self.logger.setLevel(logging.DEBUG)
        self.handler_file = logging.FileHandler("logs.txt")
        self.handler_file.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s : %(message)s'))
        self.handler_file.setLevel(logging.DEBUG)
        self.logger.addHandler(self.handler_file)

        self.handler_stream = logging.StreamHandler()
        self.handler_stream.setLevel(logging.DEBUG)
        self.handler_stream.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s : %(message)s'))
        self.logger.addHandler(self.handler_stream)

    def debug(self, msg : str):
        self.logger.debug(msg)

    def info(self, msg : str):
        self.logger.info(msg)

    def warning(self, msg : str):
        self.logger.warning(msg)

    def error(self, msg : str):
        self.logger.error(msg)

if __name__ == '__main__':
    logger = Logger()
    logger.debug("test blabla")
    logger.info("test blabla 2")
    logger.warning("test blabla 3")
    logger.error("test blabla 4")
