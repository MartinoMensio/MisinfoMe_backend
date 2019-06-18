import abc

class IExternalSource(abc.ABC):
    @abc.abstractmethod
    def update(self):
        """This method makes the external source update its data"""
        pass

class ISourceRater(abc.ABC):
    @abc.abstractmethod
    def rate_source(self, source):
        """Rates a source"""
        pass