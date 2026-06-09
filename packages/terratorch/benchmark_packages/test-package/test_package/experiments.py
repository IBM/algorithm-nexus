# Copyright IBM Corporation 2025, 2026
# SPDX-License-Identifier: MIT

"""Custom experiments for terratorch benchmarks."""

from typing import Any

from orchestrator.modules.actuators.custom_experiments import custom_experiment


@custom_experiment(output_property_identifiers=["result"])
def echo_experiment(input_string: str) -> dict[str, Any]:
    """
    Simple custom experiment that echoes the input string.

    This is a minimal example demonstrating the structure required
    by ADO (Automated Design Optimization).

    Parameters
    ----------
    input_string : str
        The string to echo back

    Returns
    -------
    dict[str, Any]
        Dictionary containing 'result' key with the input string
    """
    return {
        "result": input_string,
    }
