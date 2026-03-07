"""test_fallback.py — Comprehensive tests for all fallback layers"""
import pytest
from app.services import fallback_engine, procedural_gen, conceptual_viz, classifier
from app.models.schemas import ConceptResponse


def make_concept(query, ctype, components=None, related=None):
    return ConceptResponse(
        query=query, category="test", type=ctype,
        components=components or ["part_1","part_2","part_3"],
        related_terms=related or ["term_1","term_2"],
        spatial_description=f"A {query} structure",
        search_keywords=[query.lower()] + (related or []),
    )

ABSTRACT = make_concept("Democracy","abstract",["citizens","voting","representation","governance"])
ALGO     = make_concept("Binary Search Tree","algorithmic",["root","node","left_child","right_child"])
PHYSICAL = make_concept("Water Molecule","physical",["oxygen","hydrogen","bond"])
BIO      = make_concept("DNA","biological",["double helix","nucleotide","base pair","strand"])
GLUCOSE  = make_concept("Glucose","physical",["carbon","hydrogen","oxygen","ring","hydroxyl"])
INCLINE  = make_concept("Inclined Plane","physical",["ramp","surface","angle","gravity","friction"])
NEURAL   = make_concept("Neural Network","algorithmic",["input layer","hidden layer","output layer","neuron"])
CELL     = make_concept("Cell","biological",["nucleus","membrane","cytoplasm","mitochondria"])
UNKNOWN  = make_concept("Quantum Entanglement","physical",["particle","spin","correlation"])


def test_procedural_never_crashes():
    for c in [ALGO, PHYSICAL, BIO, GLUCOSE, INCLINE, NEURAL, CELL, UNKNOWN]:
        assert procedural_gen.generate(c) is not None

def test_procedural_returns_layer2():
    r = procedural_gen.generate(ALGO)
    assert r.layer_used == 2
    assert r.geometry is not None
    assert len(r.geometry) >= 10

def test_procedural_shapes_valid():
    r = procedural_gen.generate(ALGO)
    for s in r.geometry:
        assert s.shape in {"sphere","cylinder","box","cone"}
        assert len(s.position) == 3
        assert s.color.startswith("#")

def test_procedural_glucose():
    r = procedural_gen.generate(GLUCOSE)
    assert r.geometry and len(r.geometry) > 5

def test_procedural_inclined_plane():
    r = procedural_gen.generate(INCLINE)
    labels = [s.label for s in r.geometry if s.label]
    assert any(l in ["ramp","Fg","FN","Ff"] for l in labels)

def test_conceptual_layer3():
    r = conceptual_viz.generate(ABSTRACT)
    assert r.layer_used == 3
    assert r.geometry is not None

def test_classifier_algorithmic():
    s = classifier.get_strategy("algorithmic")
    assert s[0] == "procedural"

def test_classifier_abstract():
    s = classifier.get_strategy("abstract")
    assert s[0] == "conceptual_viz"

@pytest.mark.asyncio
async def test_engine_never_crashes():
    r = await fallback_engine.run(ABSTRACT)
    assert r is not None and r.explanation

@pytest.mark.asyncio
async def test_abstract_hits_layer3():
    r = await fallback_engine.run(ABSTRACT)
    assert r.layer_used == 3

@pytest.mark.asyncio
async def test_algo_hits_layer2():
    r = await fallback_engine.run(ALGO)
    assert r.layer_used in [1, 2]
    assert r.geometry is not None

@pytest.mark.asyncio
async def test_unknown_always_responds():
    r = await fallback_engine.run(UNKNOWN)
    assert r is not None and r.layer_used >= 2
