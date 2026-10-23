from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class Evidence(Model):
    id: str
    title: str
    page: int = Field(ge=1)
    printed_page: str
    bbox: tuple[float,float,float,float]
    context_bboxes: list[tuple[float,float,float,float]] = []
    text: str
    context: str = ""
    aliases: list[str] = []
    summary: str = ""
    curated: bool = False
    context_only: bool = False

class Parameter(Model):
    id: str
    symbol: str
    name: str
    rating: Literal["absolute_maximum","recommended","electrical"]
    minimum: float | str | None = None
    typical: float | str | None = None
    maximum: float | str | None = None
    unit: str
    conditions: str
    notes: list[str] = []
    evidence_ids: list[str]
    review: str

class Hit(Model):
    evidence_id: str
    score: float

class RuleResult(Model):
    rule: str
    title: str
    status: Literal["satisfied","violated","needs_information","invalid","estimated"]
    message: str
    evidence_ids: list[str]
    value: float | None = None
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    fields: list[str] = []

class OperatingPoint(Model):
    vdd: str | None = None
    tj: str | None = None
    frequency: str | None = None
    resistance: str | None = None
    capacitance: str | None = None
    ambient_temperature: str | None = None
    resistance_tolerance: str | None = None
    capacitance_tolerance: str | None = None

class ConditionPoint(Model):
    vdd: str | None = None
    temperature: str | None = None
    temperature_kind: Literal["test", "ambient", "junction", "unknown"] = "unknown"
    frequency: str | None = None
    resistance: str | None = None
    capacitance: str | None = None
    load_capacitance: str | None = None
    vfb: str | None = None
    comp: str | None = None
    comp_equals_fb: bool | None = None
    driver_switching: bool | None = None

class ConditionMatch(Model):
    parameter_id: str
    status: Literal["applicable", "not_applicable", "needs_information", "not_evaluated", "invalid"]
    reasons: list[str]
    evidence_ids: list[str]

class Result(Model):
    chip_id: str = "tps40200"
    status: Literal["answered","evidence_only","needs_information","not_found","unsupported","invalid"]
    question: str
    answer: str
    inputs: dict[str,str | None] = {}
    parameters: list[Parameter] = []
    checks: list[RuleResult] = []
    evidence_ids: list[str] = []
    hits: list[Hit] = []
    notices: list[str] = []
    source_sha256: str = ""
    source_revision: str = "SLUS659G (Rev. G)"
    condition_inputs: dict[str, str | bool | None] = {}
    applicability: list[ConditionMatch] = []
    condition_errors: dict[str, str] = {}

RATING_LABELS={"absolute_maximum":"绝对最大额定值","recommended":"推荐工作条件","electrical":"电气特性"}
STATUS_LABELS={"answered":"已找到参数","evidence_only":"相关证据","needs_information":"信息不足","not_found":"未找到证据","unsupported":"当前不支持","invalid":"输入需要修改"}
RULE_LABELS={"satisfied":"满足该项","violated":"不满足该项","needs_information":"信息不足","invalid":"输入需要修改","estimated":"标称估算"}
