from info_model import OUTGOING_INFORMATION_MODEL, INCOME_INFORMATION_MODEL
import rdflib

g = rdflib.Graph()
MF = rdflib.Namespace("https://moneyflow.sep.dev/")
g.namespace_manager.bind("mf", MF)
g.namespace_manager.bind("skos", rdflib.SKOS)


def _slug(key: str):
    return key.replace(" ", "_").replace("&", "_").replace("/", "")


def _add_to_graph(key: str, model):
    g.add(
        (
            MF[_slug(key)],
            rdflib.RDFS.label,
            rdflib.Literal(key.casefold().capitalize()),
        )
    )
    g.add((MF[_slug(key)], rdflib.SKOS.prefLabel, rdflib.Literal(key)))
    g.add((MF[_slug(key)], rdflib.RDF.type, MF["spend"]))
    if isinstance(model[key], dict):
        for child in model[key]:
            _add_to_graph(child, model[key])
            g.add((MF[_slug(key)], MF.hasChild, MF[_slug(child)]))


for k in OUTGOING_INFORMATION_MODEL:
    _add_to_graph(k, OUTGOING_INFORMATION_MODEL)

g.serialize("graph.ttl")
