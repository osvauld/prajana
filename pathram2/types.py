"""types.py — Node, Edge dataclasses and relation/type/tag constants."""

from dataclasses import dataclass, field
from datetime import datetime


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --- Relation constants ---
# Core 10 visheshanam (same as proof graph) + pathram extensions

VISHESHANAM = {
    # Core 10 — same semantics as the proof graph
    "swarupa":       "identity (X IS Y)",
    "abheda":        "non-different / consolidated-into / same-as",
    "drishthanta":   "evidence / example / witness",
    "sthita":        "foundation / belongs-to / child-of (hierarchy)",
    "yukta":         "connection / related-to (semantic)",
    "siddha":        "proof / verified",
    "kriya":         "function / acts-as / operation",
    "phala":         "consequence / results-in / produces",
    "janya":         "origin / born-from / source",
    "pratipaksha":   "inverse / supersedes / replaces",
}

# Pathram extensions — domain-specific edges
EXTENSIONS = {
    "krama":         "ordered sequence (step chain, temporal ordering)",
    "branches-from": "tangent origin (with reason in edge shabda)",
    "returns-to":    "return from tangent",
    "fixes":         "corrects a problem",
    "references":    "documentation link",
    "depends-on":    "prerequisite / blocker",
}

RELATIONS = {**VISHESHANAM, **EXTENSIONS}

# --- Node type constants ---

NODE_TYPES = {
    "philosophy": "Enduring truths, path-agnostic",
    "discovery":  "Findings during work",
    "session":    "Journal entry, what happened",
    "step":       "Actionable work unit",
    "branch":     "Tangent decision point",
    "note":       "Implementation detail",
    "quirk":      "Gotcha / known issue",
    "report":     "Compiled/generated view",
    "doc":        "Container / topic grouping",
}

# --- Tag constants ---

TAGS = {
    "active":       "Current, applicable",
    "done":         "Completed",
    "consolidated": "Merged into another node",
    "abandoned":    "Dropped, never finished",
    "wrong":        "Incorrect",
    "deferred":     "Intentionally postponed",
}

# --- Dataclasses ---


@dataclass
class Node:
    id: str
    type: str
    title: str
    body: str = ""
    tag: str = "active"
    shabda: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "tag": self.tag,
            "shabda": self.shabda,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Node":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Edge:
    source: str
    target: str
    relation: str
    shabda: dict = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    @property
    def key(self) -> str:
        """Deterministic edge key for storage."""
        return f"{self.source}|{self.relation}|{self.target}"

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "shabda": self.shabda,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Edge":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
