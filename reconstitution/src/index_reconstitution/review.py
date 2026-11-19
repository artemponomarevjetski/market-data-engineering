"""Dated provenance and explicit methodology checks for a review decision.

These contracts aggregate caller-supplied rules and evidence. They do not infer
provider thresholds, produce index weights, or authorize a trading basket.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
import math

from ._validation import (
    ensure_aware, ensure_date, ensure_methodology_match, ensure_sha256,
    ensure_tuple, require_nonempty,
)

class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNRESOLVED = "UNRESOLVED"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ReviewCutoff:
    timestamp: datetime
    methodology_version_id: str

    def __post_init__(self) -> None:
        ensure_aware(self.timestamp, "review cutoff")
        require_nonempty(self.methodology_version_id, "methodology_version_id")


@dataclass(frozen=True)
class SecurityIdentity:
    security_id: str
    issuer_id: str
    ticker: str
    exchange: str
    valid_from: date
    valid_to: date | None = None
    isin: str | None = None
    share_class: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("security_id", "issuer_id", "ticker", "exchange"):
            require_nonempty(getattr(self, field_name), field_name)
        ensure_date(self.valid_from, "valid_from")
        if self.valid_to is not None:
            ensure_date(self.valid_to, "valid_to")
            if self.valid_to < self.valid_from:
                raise ValueError("security validity end precedes start")
        for field_name in ("isin", "share_class"):
            if getattr(self, field_name) is not None:
                require_nonempty(getattr(self, field_name), field_name)

    def is_valid_on(self, observation_date: date) -> bool:
        ensure_date(observation_date, "observation_date")
        return self.valid_from <= observation_date and (
            self.valid_to is None or observation_date <= self.valid_to
        )


@dataclass(frozen=True)
class Provenance:
    source: str
    source_record_id: str
    issuer_id: str
    security_id: str | None
    observation_date: date
    reporting_period: str | None
    availability_time: datetime | None
    review_cutoff: ReviewCutoff
    methodology_version_id: str
    content_sha256: str | None = None
    transformations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("source", "source_record_id", "issuer_id"):
            require_nonempty(getattr(self, field_name), field_name)
        if self.security_id is not None:
            require_nonempty(self.security_id, "security_id")
        ensure_date(self.observation_date, "observation_date")
        if self.reporting_period is not None:
            require_nonempty(self.reporting_period, "reporting_period")
        if self.availability_time is not None:
            ensure_aware(self.availability_time, "availability_time")
        ensure_methodology_match(self.methodology_version_id,
                                 self.review_cutoff.methodology_version_id)
        if self.content_sha256 is not None:
            ensure_sha256(self.content_sha256)
        ensure_tuple(self.transformations, "transformations")
        for transformation in self.transformations:
            require_nonempty(transformation, "transformation")


@dataclass(frozen=True)
class AvailabilityResult:
    status: Status
    reason: str


class PointInTimeError(ValueError):
    """An input cannot be used at the requested historical cutoff."""


def check_observation_availability(
    *, observation_date: date, availability_time: datetime | None, cutoff: datetime
) -> AvailabilityResult:
    """Check dates independently of a still-unresolved methodology or identity.

    A future observation is unusable even when publication time is unknown.
    Naive timestamps cannot silently acquire a timezone.
    """
    ensure_date(observation_date, "observation_date")
    ensure_aware(cutoff, "review cutoff")
    if availability_time is not None:
        ensure_aware(availability_time, "availability_time")
    if observation_date > cutoff.date():
        return AvailabilityResult(Status.FAIL, "observation date is after review cutoff")
    if availability_time is None:
        return AvailabilityResult(Status.UNRESOLVED, "availability time is unknown")
    if availability_time > cutoff:
        return AvailabilityResult(Status.FAIL, "input became available after review cutoff")
    return AvailabilityResult(Status.PASS, "input was available by review cutoff")


def check_availability(
    provenance: Provenance, cutoff: ReviewCutoff | None = None
) -> AvailabilityResult:
    """Validate bound context; unknown availability is unresolved and equality passes."""
    requested = cutoff if cutoff is not None else provenance.review_cutoff
    if provenance.methodology_version_id != requested.methodology_version_id:
        return AvailabilityResult(Status.FAIL, "methodology version mismatch")
    if provenance.review_cutoff != requested:
        return AvailabilityResult(Status.FAIL, "review cutoff context mismatch")
    return check_observation_availability(
        observation_date=provenance.observation_date,
        availability_time=provenance.availability_time,
        cutoff=requested.timestamp,
    )


def require_available(provenance: Provenance, cutoff: ReviewCutoff | None = None) -> None:
    """Raise for failed or unresolved inputs so callers cannot treat them as usable."""
    result = check_availability(provenance, cutoff)
    if result.status is not Status.PASS:
        raise PointInTimeError(f"{result.status.value}: {result.reason}")


@dataclass(frozen=True)
class HumanApproval:
    """Approval of an individual judgment; this alone does not authorize a basket."""

    reviewer_id: str
    approved_at: datetime
    rationale: str

    def __post_init__(self) -> None:
        require_nonempty(self.reviewer_id, "reviewer_id")
        ensure_aware(self.approved_at, "approved_at")
        require_nonempty(self.rationale, "rationale")


@dataclass(frozen=True)
class RuleException:
    reason: str
    approval: HumanApproval | None = None

    def __post_init__(self) -> None:
        require_nonempty(self.reason, "exception reason")
        if self.approval is not None and not isinstance(self.approval, HumanApproval):
            raise ValueError("exception approval must be a typed HumanApproval")


@dataclass(frozen=True)
class MethodologyRule:
    rule_id: str
    description: str
    mandatory: bool = True
    required_evidence: tuple[str, ...] = ()
    allows_exception: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self.rule_id, "rule_id")
        require_nonempty(self.description, "description")
        if type(self.mandatory) is not bool or type(self.allows_exception) is not bool:
            raise ValueError("methodology rule flags must be Boolean")
        ensure_tuple(self.required_evidence, "required_evidence")
        if len(set(self.required_evidence)) != len(self.required_evidence):
            raise ValueError("required evidence identifiers must be unique")
        for evidence_id in self.required_evidence:
            require_nonempty(evidence_id, "required evidence identifier")


@dataclass(frozen=True)
class MethodologyVersion:
    version_id: str
    source: str
    effective_from: date
    rules: tuple[MethodologyRule, ...]
    effective_to: date | None = None
    confirmed: bool = False

    def __post_init__(self) -> None:
        require_nonempty(self.version_id, "version_id")
        require_nonempty(self.source, "source")
        if type(self.confirmed) is not bool:
            raise ValueError("methodology confirmation must be Boolean")
        ensure_date(self.effective_from, "effective_from")
        if self.effective_to is not None:
            ensure_date(self.effective_to, "effective_to")
            if self.effective_to < self.effective_from:
                raise ValueError("methodology validity end precedes start")
        ensure_tuple(self.rules, "rules")
        if any(not isinstance(rule, MethodologyRule) for rule in self.rules):
            raise ValueError("methodology rules must be typed MethodologyRule records")
        if len({rule.rule_id for rule in self.rules}) != len(self.rules):
            raise ValueError("methodology rule identifiers must be unique")

    def is_effective_on(self, review_date: date) -> bool:
        ensure_date(review_date, "review_date")
        return self.effective_from <= review_date and (
            self.effective_to is None or review_date <= self.effective_to
        )


@dataclass(frozen=True)
class CalculationWindow:
    start: date
    end: date

    def __post_init__(self) -> None:
        ensure_date(self.start, "calculation window start")
        ensure_date(self.end, "calculation window end")
        if self.end < self.start:
            raise ValueError("calculation window end precedes start")


@dataclass(frozen=True)
class RuleCheckResult:
    rule_id: str
    methodology_version_id: str
    status: Status
    evidence: tuple[Provenance, ...] = ()
    calculation_window: CalculationWindow | None = None
    calculation: str = ""
    result: str | float | None = None
    exception: RuleException | None = None
    reviewer_approval: HumanApproval | None = None

    def __post_init__(self) -> None:
        require_nonempty(self.rule_id, "rule_id")
        require_nonempty(self.methodology_version_id, "methodology_version_id")
        if not isinstance(self.status, Status):
            raise ValueError("status must be a Status")
        ensure_tuple(self.evidence, "evidence")
        for provenance in self.evidence:
            if not isinstance(provenance, Provenance):
                raise ValueError("rule evidence must be a typed Provenance record")
            if provenance.methodology_version_id != self.methodology_version_id:
                raise ValueError("rule evidence methodology version does not match the check")
        if self.exception is not None and not isinstance(self.exception, RuleException):
            raise ValueError("rule exception must be a typed RuleException")
        if self.reviewer_approval is not None and not isinstance(self.reviewer_approval, HumanApproval):
            raise ValueError("reviewer approval must be a typed HumanApproval")
        if self.calculation_window is not None and not isinstance(self.calculation_window, CalculationWindow):
            raise ValueError("calculation window must be a typed CalculationWindow")
        if isinstance(self.result, float) and not math.isfinite(self.result):
            raise ValueError("numeric rule result must be finite")


@dataclass(frozen=True)
class EligibilityAssessment:
    security_id: str
    methodology_version_id: str
    review_cutoff: ReviewCutoff
    status: EligibilityStatus
    rule_checks: tuple[RuleCheckResult, ...]
    unresolved_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        require_nonempty(self.security_id, "security_id")
        require_nonempty(self.methodology_version_id, "methodology_version_id")
        if not isinstance(self.status, EligibilityStatus):
            raise ValueError("status must be an EligibilityStatus")
        ensure_tuple(self.rule_checks, "rule_checks")
        ensure_tuple(self.unresolved_reasons, "unresolved_reasons")
        # An unresolved assessment must preserve conflicting inputs for audit.
        if self.status == EligibilityStatus.ELIGIBLE:
            ensure_methodology_match(self.methodology_version_id,
                                     self.review_cutoff.methodology_version_id)
            if len({check.rule_id for check in self.rule_checks}) != len(self.rule_checks):
                raise ValueError("eligible rule check identifiers must be unique")
            for check in self.rule_checks:
                if check.methodology_version_id != self.methodology_version_id:
                    raise ValueError("eligible check methodology version does not match")
                for provenance in check.evidence:
                    if provenance.security_id not in (None, self.security_id):
                        raise ValueError("eligible evidence belongs to another security")
                    if provenance.review_cutoff != self.review_cutoff:
                        raise ValueError("eligible evidence review cutoff does not match")
        for reason in self.unresolved_reasons:
            require_nonempty(reason, "unresolved reason")


def assess_eligibility(
    security: SecurityIdentity,
    methodology: MethodologyVersion,
    cutoff: ReviewCutoff,
    checks: tuple[RuleCheckResult, ...],
    *,
    identity_resolved: bool = True,
    required_review_approvals_complete: bool = True,
) -> EligibilityAssessment:
    """Aggregate declared checks: unresolved prerequisites precede failures.

    Mandatory check evidence is validated before any final eligibility result.
    Optional failures remain separate records and cannot veto eligibility.
    Similarity is deliberately absent from this decision contract.
    """
    if type(identity_resolved) is not bool or type(required_review_approvals_complete) is not bool:
        raise ValueError("review prerequisite flags must be Boolean")
    ensure_tuple(checks, "checks")
    if any(not isinstance(check, RuleCheckResult) for check in checks):
        raise ValueError("checks must contain typed RuleCheckResult records")
    unresolved: list[str] = []
    if not identity_resolved:
        unresolved.append("security identity is unresolved")
    if not required_review_approvals_complete:
        unresolved.append("required eligibility-review approvals are incomplete")
    if not methodology.confirmed:
        unresolved.append("methodology version is unconfirmed")
    if methodology.version_id != cutoff.methodology_version_id:
        unresolved.append("methodology does not match review cutoff")
    day = cutoff.timestamp.date()
    if day < methodology.effective_from or (
        methodology.effective_to is not None and day > methodology.effective_to
    ):
        unresolved.append("methodology is outside its effective dates")
    if day < security.valid_from or (security.valid_to is not None and day > security.valid_to):
        unresolved.append("security identity is outside its validity dates")

    mandatory = tuple(rule for rule in methodology.rules if rule.mandatory)
    if not mandatory:
        unresolved.append("required-check set is empty")
    by_id: dict[str, RuleCheckResult] = {}
    for check in checks:
        if check.rule_id in by_id:
            unresolved.append(f"duplicate check for rule {check.rule_id}")
        by_id[check.rule_id] = check
        if check.rule_id not in {rule.rule_id for rule in methodology.rules}:
            unresolved.append(f"unknown rule {check.rule_id}")
        if check.methodology_version_id != methodology.version_id:
            unresolved.append(f"{check.rule_id}: check methodology mismatch")
        for item in check.evidence:
            if item.issuer_id != security.issuer_id:
                unresolved.append(f"{check.rule_id}: evidence issuer mismatch")
            if item.security_id is not None and item.security_id != security.security_id:
                unresolved.append(f"{check.rule_id}: evidence security mismatch")
            availability = check_availability(item, cutoff)
            if availability.status is not Status.PASS:
                unresolved.append(f"{check.rule_id}: {availability.reason}")
        if check.calculation_window is not None and check.calculation_window.end > day:
            unresolved.append(f"{check.rule_id}: calculation window extends past cutoff")

    failed = False
    for rule in mandatory:
        check = by_id.get(rule.rule_id)
        if check is None:
            unresolved.append(f"{rule.rule_id}: mandatory check is missing")
            continue
        if check.status is Status.UNRESOLVED:
            unresolved.append(f"{rule.rule_id}: mandatory result is unresolved")
        evidence_ids = {item.source_record_id for item in check.evidence}
        if not set(rule.required_evidence).issubset(evidence_ids):
            unresolved.append(f"{rule.rule_id}: required evidence is missing")
        exception = check.exception
        exception_allowed = False
        if exception is not None:
            if not rule.allows_exception:
                unresolved.append(f"{rule.rule_id}: methodology does not allow this exception")
            elif exception.approval is None:
                unresolved.append(f"{rule.rule_id}: exception lacks human approval")
            else:
                exception_allowed = True
        if check.status is Status.FAIL and not exception_allowed:
            failed = True

    status = (
        EligibilityStatus.UNRESOLVED
        if unresolved
        else EligibilityStatus.INELIGIBLE
        if failed
        else EligibilityStatus.ELIGIBLE
    )
    return EligibilityAssessment(
        security_id=security.security_id,
        methodology_version_id=methodology.version_id,
        review_cutoff=cutoff,
        status=status,
        rule_checks=checks,
        unresolved_reasons=tuple(dict.fromkeys(unresolved)),
    )
