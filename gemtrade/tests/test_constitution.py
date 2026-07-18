"""Tests for the constitution module."""

import pytest
from gemtrade.core.constitution import (
    CONSTITUTION,
    validate_signal,
    RuleSeverity,
)


def test_constitution_has_rules():
    """Constitution should have rules defined."""
    assert len(CONSTITUTION) > 0


def test_stop_loss_required():
    """Trades without stop loss should be rejected."""
    signal = {"position_pct": 2.0}  # No stop loss
    state = {"open_position_count": 0, "exposure_pct": 0}
    
    result = validate_signal(signal, state)
    
    assert not result.allowed
    assert "Stop Loss" in (result.reason or "")


def test_valid_signal_passes():
    """Valid signals should pass validation."""
    signal = {
        "stop_loss": 100.0,
        "position_pct": 3.0,
        "risk_pct": 1.5,
    }
    state = {
        "open_position_count": 1,
        "exposure_pct": 20.0,
        "daily_loss_pct": 1.0,
        "weekly_loss_pct": 5.0,
        "drawdown_pct": 10.0,
        "consecutive_losses": 2,
    }
    
    result = validate_signal(signal, state)
    
    assert result.allowed


def test_position_size_limit():
    """Positions over 5% should be rejected."""
    signal = {
        "stop_loss": 100.0,
        "position_pct": 7.0,  # Over limit
        "risk_pct": 1.0,
    }
    state = {"open_position_count": 0, "exposure_pct": 0}
    
    result = validate_signal(signal, state)
    
    assert not result.allowed


def test_daily_loss_halt():
    """Should halt when daily loss exceeds 3%."""
    signal = {"stop_loss": 100.0, "position_pct": 2.0, "risk_pct": 1.0}
    state = {
        "open_position_count": 0,
        "exposure_pct": 0,
        "daily_loss_pct": 4.0,  # Over limit
        "weekly_loss_pct": 4.0,
        "drawdown_pct": 5.0,
        "consecutive_losses": 0,
    }
    
    result = validate_signal(signal, state)
    
    assert not result.allowed
    assert result.must_halt


def test_concurrent_positions_limit():
    """Should reject when at max concurrent positions."""
    signal = {"stop_loss": 100.0, "position_pct": 2.0, "risk_pct": 1.0}
    state = {
        "open_position_count": 3,  # At limit
        "exposure_pct": 30.0,
        "daily_loss_pct": 0,
        "weekly_loss_pct": 0,
        "drawdown_pct": 0,
        "consecutive_losses": 0,
    }
    
    result = validate_signal(signal, state)
    
    assert not result.allowed
