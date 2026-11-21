from rmti.cli import main


def test_selfcheck_exit_zero(capsys):
    assert main(["selfcheck"]) == 0
    assert "MISMATCH" not in capsys.readouterr().out
