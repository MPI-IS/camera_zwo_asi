def _estimate_darkframe_time(
    control_ranges: typing.Dict[str, ControlRange],
    avg_over: int,
    exposure: typing.Optional[int] = None,
) -> typing.Tuple[int, int]:
    """
    Return an estimation of how long capturing all darkframes will
    take (in seconds). If "Exposure" is in the control range,
    then the corresponding values will be used for the evaluation.
    Else, 'exposure' should not be None.

    Returns
    -------
       the expected duration (in seconds) and the number of pictures
       that will be taken.
    """

    controls = list(control_ranges.keys())
    if "Exposure" in controls:
        exp_index = controls.index("Exposture")
    else:
        exp_index = None

    all_controls = list(
        _iterate_controls([control_ranges[control] for control in controls])
    )

    nb_pics = len(all_controls) * avg_over

    if exp_index is None:
        return len(all_controls) * avg_over * exposure, nb_pics

    return (
        sum([ac[exp_index] / 1e6 for ac in all_controls]) * avg_over * exposure,
        nb_pics,
    )


def darkframes(config: Path, output: Path, camera: Camera) -> None:

    control_ranges, roi, avg_over = ControlRange.from_toml(config)

    duration, nb_pics = _estimage_darkframe_time(
        control_ranges,
        avg_over,
    )
