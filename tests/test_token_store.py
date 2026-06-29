import stat

from app.token_store import TokenSet, TokenStore


def test_token_store_round_trip_uses_private_permissions(tmp_path) -> None:
    path = tmp_path / "tokens.json"
    store = TokenStore(path)
    tokens = TokenSet(
        access_token="access",
        refresh_token="refresh",
        expires_at=1234567890,
        scope="accounts:read",
    )

    store.save(tokens)

    assert store.load() == tokens
    assert stat.S_IMODE(path.stat().st_mode) == 0o600

