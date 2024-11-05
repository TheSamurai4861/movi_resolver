import importlib
import os
import re
from urllib.parse import urlparse

class HostedMediaFile:
    def __init__(self, url=''):
        if not url:
            raise ValueError('Set either url')
        self._url = 'http:%s' % url if url.startswith("//") else url
        self._domain = self.__top_domain(self._url)
        self.__resolvers = self.__find_resolver_for_domain(self._domain)
    
    def __top_domain(self, url):
        elements = urlparse(url)
        domain = elements.netloc or elements.path
        domain = domain.split('@')[-1].split(':')[0]
        regex = r"(?:www\.)?([\w\-]*\.[\w\-]{2,5}(?:\.[\w\-]{2,5})?)$"
        res = re.search(regex, domain)
        if res:
            domain = '.'.join(res.group(1).split('.')[-2:])
        return domain.lower()
    
    def __find_resolver_for_domain(self, domain):
        """Recherche et retourne les résolveurs pour le domaine spécifié."""
        relevant_resolvers = []
        plugins_path = "resolverurl/plugins"  # Remplacez par le chemin absolu si nécessaire

        # Parcourt chaque fichier dans le dossier plugins
        for filename in os.listdir(plugins_path):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = f"resolverurl.plugins.{filename[:-3]}"
                module = importlib.import_module(module_name)

                # Recherche des classes dans le module qui ont un domaine correspondant
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and hasattr(attr, 'domains'):
                        # Vérifie si le domaine est supporté par le resolver
                        if domain in attr.domains:
                            print(f"Found resolver {attr.__name__} for domain {domain}")
                            relevant_resolvers.append(attr)
        
        if not relevant_resolvers:
            print(f"No resolver found for domain {domain}")
        
        return relevant_resolvers
    
    def resolve(self):
        """
        Simplified resolve method for resolving the media URL.
        """
        if not self.__resolvers:
            print(f"No resolvers found for domain {self._domain}")
            return False

        # Assume there is only one resolver for the domain
        resolver_class = self.__resolvers[0]
        resolver = resolver_class()  # Instantiate the resolver

        try:
            # Extract host and media ID from the URL
            self._host, self._media_id = resolver.get_host_and_id(self._url)
            
            # Get the media URL
            stream_url = resolver.get_media_url(self._host, self._media_id)

            # Ensure the stream URL has the correct protocol
            if stream_url and stream_url.startswith("//"):
                stream_url = 'http:%s' % stream_url

            if stream_url:
                print(f"Resolved media URL: {stream_url}")
                return stream_url
            else:
                print(f"Failed to resolve URL with {resolver.name}")
                return False

        except Exception as e:
            print(f"Error resolving URL with {resolver.name}: {e}")
            return False
