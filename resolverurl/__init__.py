import importlib
import os
from resolverurl.plugins import __resolve_generic__

def find_relevant_resolvers(domain):
    relevant_resolvers = []
    plugins_path = "resolverurl/plugins"  # Remplacez par le chemin absolu si nécessaire

    for filename in os.listdir(plugins_path):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"resolverurl.plugins.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                importlib.reload(module)  # Recharge le module pour s'assurer qu'il est à jour
            except Exception as e:
                print(f"Erreur lors du chargement du module {module_name}: {e}")
                continue
            
            # Recherche des sous-classes de ResolveGeneric
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, __resolve_generic__.ResolveGeneric) and attr is not __resolve_generic__.ResolveGeneric:
                    if hasattr(attr, 'domains'):
                        print(f"Checking resolver {attr.__name__} with domains {attr.domains}")
                        if domain in attr.domains:
                            relevant_resolvers.append(attr)
    
    return relevant_resolvers
