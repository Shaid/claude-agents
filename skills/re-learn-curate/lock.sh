#!/usr/bin/env bash
# Curation lock for the game-re knowledge base.
#
#   lock.sh acquire <label>   -> prints "token=<token>" and exits 0, or "held by: ..." and exits 1
#   lock.sh heartbeat         -> refreshes the lock's mtime (call after each inbox item)
#   lock.sh release <token>   -> removes the lock only if <token> still owns it
#   lock.sh status            -> free | held by: ... [STALE]
#
# mkdir is the atomic acquire. A lock whose directory mtime is older than
# STALE_MIN minutes is broken by atomic rename (never rm in place), and the
# renamed copy's owner token is re-checked so a breaker that raced another
# breaker puts a fresh lock back instead of deleting it.
set -u
L="$HOME/.claude/agents/.re-learn.lock"
STALE_MIN=90

owner() { cat "$L/owner" 2>/dev/null; }

try_acquire() {
  mkdir "$L" 2>/dev/null || return 1
  printf '%s\n' "$TOKEN" > "$L/owner"
}

case "${1:-}" in
acquire)
  TOKEN="$(date -u +%FT%TZ)-$$-$RANDOM-${2:-unknown}"
  if try_acquire; then echo "token=$TOKEN"; exit 0; fi
  if [ -n "$(find "$L" -maxdepth 0 -mmin +"$STALE_MIN" 2>/dev/null)" ]; then
    old="$(owner)"
    tmp="$L.stale.$$.$RANDOM"
    if mv -T "$L" "$tmp" 2>/dev/null; then
      if [ "$(cat "$tmp/owner" 2>/dev/null)" = "$old" ]; then
        rm -rf "$tmp"
        if try_acquire; then echo "token=$TOKEN"; echo "broke stale lock: $old" >&2; exit 0; fi
      else
        # We renamed a lock someone else had just taken: restore it.
        mv -T "$tmp" "$L" 2>/dev/null || rm -rf "$tmp"
      fi
    fi
  fi
  echo "held by: $(owner || echo '?')"
  exit 1
  ;;
heartbeat)
  [ -d "$L" ] && touch "$L"
  ;;
release)
  if [ "$(owner)" = "${2:-}" ]; then rm -rf "$L"; echo released
  else echo "not released: lock is owned by '$(owner)'" >&2; exit 1; fi
  ;;
status)
  if [ -d "$L" ]; then
    echo "held by: $(owner)"
    [ -n "$(find "$L" -maxdepth 0 -mmin +"$STALE_MIN" 2>/dev/null)" ] && echo STALE
  else
    echo free
  fi
  ;;
*)
  echo "usage: $0 acquire <label> | heartbeat | release <token> | status" >&2
  exit 2
  ;;
esac
