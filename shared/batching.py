"""Pengelompokan objek utuh dengan toleransi sisa hingga 10 kolom."""

from typing import Callable, Sequence, TypeVar


T = TypeVar("T")
MAX_MERGED_REMAINDER = 10


def chunk_with_small_remainder(items: Sequence[T], max_size: int) -> list[list[T]]:
    """Gabungkan sisa 1–10 item ke batch sebelumnya."""
    chunks = []
    for start in range(0, len(items), max_size):
        remaining = len(items) - start
        if remaining <= max_size + MAX_MERGED_REMAINDER:
            chunks.append(list(items[start:]))
            break
        chunks.append(list(items[start:start + max_size]))
    return chunks


def group_by_size(items: list[T], max_items: int, max_size: int,
                  size: Callable[[T], int]) -> list[list[T]]:
    groups: list[list[T]] = []
    group: list[T] = []
    group_size = 0
    for item in items:
        item_size = size(item)
        if group and (len(group) >= max_items
                      or group_size + item_size > max_size + MAX_MERGED_REMAINDER):
            groups.append(group)
            group = []
            group_size = 0
        group.append(item)
        group_size += item_size
    if group:
        groups.append(group)
    return groups
