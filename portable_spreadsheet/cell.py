from typing import Dict, Optional, Iterable, Tuple, Callable

import numpy as np

from .word_constructor import WordConstructor
from .cell_type import CellType
from .cell_indices import CellIndices


class Cell(object):
    def __init__(self,
                 row: Optional[int] = None,
                 column: Optional[int] = None, /,  # noqa E999
                 value: Optional[float] = None, *,
                 cell_indices: CellIndices,
                 # Private arguments
                 cell_type: CellType = CellType.value_only,
                 words: Optional[WordConstructor] = None,
                 ):
        if row is not None and column is None \
                or row is None and column is not None:
            raise ValueError("The values of 'row' and 'column' parameters have"
                             " to be either both not None or both None.")
        self.row: Optional[int] = row
        self.column: Optional[int] = column
        self._value: Optional[float] = value
        self.cell_type: CellType = cell_type
        self.cell_indices: cell_indices = cell_indices  # pass only reference

        if words is not None:
            self._constructing_words: WordConstructor = words
        else:
            self._constructing_words: WordConstructor = \
                WordConstructor.init_from_new_cell(self)

    @property
    def word(self) -> WordConstructor:
        """Return correct word. If the cell is anchored, returns just the
            coordinates. If the cell is not anchored: 1) If it is computational
            returns the building string, 2) If it is Value returns the value

        Returns:
              WordConstructor: Right word.
        """
        if self.anchored:
            return WordConstructor.reference(self)
        else:
            if self.cell_type == CellType.computational:
                return self._constructing_words
            elif self.cell_type == CellType.value_only:
                return WordConstructor.constant(self)

    @property
    def anchored(self) -> bool:
        """Return True if the cell is the part of the grid. Return False
            if it is temporarily created for the computation.

        Returns:
            bool: True/False value telling if the cell is anchored to grid.
        """
        return self.row is not None

    @property
    def coordinates(self) -> Tuple[int, int]:
        """Returns the coordinates of the cell.

        Returns:
            Tuple[int, int]: 1) row index, 2) column index
        """
        return self.row, self.column

    @coordinates.setter
    def coordinates(self, coordinates: Tuple[int, int]) -> None:
        """Set the coordinates of the grid.

        Args:
            coordinates (Tuple[int, int]): New coordinates index (row, column)
        """
        self.row = coordinates[0]
        self.column = coordinates[1]

    @property
    def value(self) -> float:
        """Return the actual numeric value of the cell.

        Returns:
            float: the numeric value of the cell.
        """
        return self._value

    def add(self, other: 'Cell', /) -> 'Cell':  # noqa E225
        """Add two values.

        Args:
            other (Cell): Another operand.

        Returns:
            Cell: self + other
        """
        return Cell(value=self.value + other.value,
                    words=WordConstructor.add(self, other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    def subtract(self, other: 'Cell', /) -> 'Cell':  # noqa E225
        """Subtract two values.

        Args:
            other (Cell): Another operand.

        Returns:
            Cell: self - other
        """
        return Cell(value=self.value - other.value,
                    words=WordConstructor.subtract(self, other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    def multiply(self, other: 'Cell', /) -> 'Cell':  # noqa E225
        """Multiply two values.

        Args:
            other (Cell): Another operand.

        Returns:
            Cell: self * other
        """
        return Cell(value=self.value * other.value,
                    words=WordConstructor.multiply(self, other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    def divide(self, other: 'Cell', /) -> 'Cell':  # noqa E225
        """Divide two values.

        Args:
            other (Cell): Another operand.

        Returns:
            Cell: self / other
        """
        return Cell(value=self.value / other.value,
                    words=WordConstructor.divide(self, other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    def power(self, other: 'Cell', /) -> 'Cell':  # noqa E225
        """Self power to other.

        Args:
            other (Cell): Another operand.

        Returns:
            Cell: self ** other
        """
        return Cell(value=self.value ** other.value,
                    words=WordConstructor.power(self, other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    # ==== OPERATOR OVERLOADING ====
    def __mul__(self, other):
        """Overload the operator '*'."""
        return self.multiply(other)

    def __sub__(self, other):
        """Overload the operator '-'."""
        return self.subtract(other)

    def __add__(self, other):
        """Overload the operator '+'."""
        return self.add(other)

    def __truediv__(self, other):
        """Overload the operator '/'."""
        return self.divide(other)

    def __pow__(self, power, modulo=None):
        """Overload the operator '**'."""
        return self.power(power)
    # ==============================

    def __str__(self) -> str:
        """Override the method __str__ to allow human-readable string
            generations of inside.

        Returns:
            str: String representation of inner value.
        """
        return str(self.parse)

    @property
    def constructing_words(self) -> WordConstructor:
        """Get the constructing words.

        Returns:
            WordConstructor: the constructing word of the cell.
        """
        return self._constructing_words

    @property
    def parse(self) -> Dict[str, str]:
        """Return the dictionary with keys: language, values: constructing
            word. This function is called when the cell should be inserted to
            a spreadsheet.

        Returns:
            Dict[str, str]: Words for each language
        """
        return self._constructing_words.parse(self)

    @staticmethod
    def sum(start_idx: Tuple[int, int], end_idx: Tuple[int, int],
            subset: Iterable['Cell']) -> 'Cell':
        return Cell._aggregate_fun(start_idx, end_idx, subset,
                                   'sum', np.sum)

    @staticmethod
    def product(start_idx: Tuple[int, int], end_idx: Tuple[int, int],
                subset: Iterable['Cell']) -> 'Cell':
        return Cell._aggregate_fun(start_idx, end_idx, subset,
                                   'product', np.prod)

    @staticmethod
    def mean(start_idx: Tuple[int, int], end_idx: Tuple[int, int],
             subset: Iterable['Cell']) -> 'Cell':
        return Cell._aggregate_fun(start_idx, end_idx, subset,
                                   'mean', np.mean)

    @staticmethod
    def min(start_idx: Tuple[int, int], end_idx: Tuple[int, int],
            subset: Iterable['Cell']) -> 'Cell':
        return Cell._aggregate_fun(start_idx, end_idx, subset,
                                   'minimum', np.min)

    @staticmethod
    def max(start_idx: Tuple[int, int], end_idx: Tuple[int, int],
            subset: Iterable['Cell']) -> 'Cell':
        return Cell._aggregate_fun(start_idx, end_idx, subset,
                                   'maximum', np.max)

    @staticmethod
    def _aggregate_fun(
            start_idx: Tuple[int, int],
            end_idx: Tuple[int, int],
            subset: Iterable['Cell'],
            grammar_method: str,
            method_np: Callable[[Iterable[float]], float]
    ) -> 'Cell':
        return Cell(value=method_np([c.value for c in subset]),
                    cell_indices=subset[0].cell_indices,
                    cell_type=CellType.computational,
                    words=subset[0]._constructing_words.aggregation(
                        start_idx, end_idx, grammar_method
                    )
                    )

    @staticmethod
    def reference(other: 'Cell', /) -> 'Cell':  # noqa E225
        """Create a reference to some anchored cell.

        Args:
            other (Cell): The cell to what reference is constructed.

        Returns:
            Cell: Cell containing only the reference to another cell.
        """
        if not other.anchored:
            raise ValueError("The referenced cell has to be anchored.")

        return Cell(value=other.value,
                    words=WordConstructor.reference(other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    @staticmethod
    def brackets(other: 'Cell', /) -> 'Cell':  # noqa E225
        """Add brackets to expression.

        Args:
            other (Cell): The expression that should be in brackets.

        Returns:
            Cell: Expression in brackets
        """
        return Cell(value=other.value,
                    words=WordConstructor.brackets(other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    @staticmethod
    def logarithm(other: 'Cell', /) -> 'Cell':  # noqa E225
        """Logarithm of the value in the cell.

        Args:
            other (Cell): Argument of the logarithm function.

        Returns:
            Cell: logarithm of the value
        """
        return Cell(value=np.log(other.value),
                    words=WordConstructor.logarithm(other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )

    @staticmethod
    def exponential(other: 'Cell', /) -> 'Cell':  # noqa E225
        """Exponential of the value in the cell.

        Args:
            other (Cell): Argument of the exponential function.

        Returns:
            Cell: exponential of the value
        """
        return Cell(value=np.exp(other.value),
                    words=WordConstructor.logarithm(other),
                    cell_indices=other.cell_indices,
                    cell_type=CellType.computational
                    )
