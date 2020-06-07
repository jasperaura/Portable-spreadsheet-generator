from numbers import Number
from typing import Tuple, List, Union, Optional, Callable
import copy

from .cell import Cell
from .cell_indices import CellIndices, T_lg_col_row
from .cell_slice import CellSlice
from .spreadsheet_utils import _Location, _Functionality, _SheetVariables
from .serialization import Serialization

# ==== TYPES ====
# Type for the sheet (list of the list of the cells)
T_sheet = List[List[Cell]]
# Sheet cell value
T_cell_val = Union[Number, Cell]
# ===============


class Spreadsheet(Serialization):
    """Simple spreadsheet that keeps tracks of each operations in defined
        languages.

    Logic allows export sheets to Excel files (and see how each cell is
        computed), to the JSON strings with description of computation e. g.
        in native language. It also allows to reconstruct behaviours in native
        Python with Numpy.

    Attributes:
        self.cell_indices (CellIndices): Define indices and the shape of the
            spreadsheet.
        _sheet (T_sheet): Array holding actual sheet.
        iloc (_Location): To make cells accessible using
            obj.iloc[integer_index_x, integer_index_y]
        loc (_Location): To make cells accessible using
            obj.loc[nick_x, nick_y]
        fn (_Functionality): To make accessible shortcuts for functionality
        var (_SheetVariables): Variables in the sheet.
    """

    def __init__(self,
                 cell_indices: CellIndices,
                 warning_logger: Optional[Callable[[str], None]] = None):
        """Initialize the spreadsheet object

        Args:
            cell_indices (CellIndices): The definition of the shape and columns
                and rows labels, help texts and descriptors.
            warning_logger (Optional[Callable[[str], None]]): Function that
                logs the warnings (or None if skipped).
        """
        # Initialise functionality for serialization:
        super().__init__(warning_logger=warning_logger)

        self._cell_indices: CellIndices = copy.deepcopy(cell_indices)

        self._sheet: T_sheet = self._initialise_array()
        # To make cells accessible using obj.iloc[pos_x, pos_y]
        self.iloc: _Location = _Location(self, True)
        # To make cells accessible using obj.loc[nick_x, nick_y]
        self.loc: _Location = _Location(self, False)
        # To make accessible shortcuts for functionality
        self.fn: _Functionality = _Functionality(self)
        # Variables of the sheet
        self.var: _SheetVariables = _SheetVariables(self)

    @staticmethod
    def create_new_sheet(
            number_of_rows: int,
            number_of_columns: int,
            rows_columns: Optional[T_lg_col_row] = None,
            /, *,  # noqa E999
            rows_labels: List[str] = None,
            columns_labels: List[str] = None,
            rows_help_text: List[str] = None,
            columns_help_text: List[str] = None,
            excel_append_row_labels: bool = True,
            excel_append_column_labels: bool = True,
            warning_logger: Optional[Callable[[str], None]] = None
    ) -> 'Spreadsheet':
        """Direct way of creating instance.

        Args:
            number_of_rows (int): Number of rows.
            number_of_columns (int): Number of columns.
            rows_columns (T_lg_col_row): List of all row names and column names
                for each user defined language.
            rows_labels (List[str]): List of masks (aliases) for row
                names.
            columns_labels (List[str]): List of masks (aliases) for column
                names.
            rows_help_text (List[str]): List of help texts for each row.
            columns_help_text (List[str]): List of help texts for each column.
            excel_append_row_labels (bool): If True, one column is added
                on the beginning of the sheet as a offset for labels.
            excel_append_column_labels (bool): If True, one row is added
                on the beginning of the sheet as a offset for labels.
            warning_logger (Optional[Callable[[str], None]]): Function that
                logs the warnings (or None if skipped).

        Returns:
            Spreadsheet: New instance of spreadsheet.
        """
        class_index = CellIndices(
            number_of_rows,
            number_of_columns,
            rows_columns,
            rows_labels=rows_labels,
            columns_labels=columns_labels,
            rows_help_text=rows_help_text,
            columns_help_text=columns_help_text,
            excel_append_row_labels=excel_append_row_labels,
            excel_append_column_labels=excel_append_column_labels,
            warning_logger=warning_logger
        )
        return Spreadsheet(class_index, warning_logger)

    def _initialise_array(self) -> T_sheet:
        """Initialise the first empty spreadsheet array on the beginning.

        Returns:
            T_sheet: New empty spreadsheet.
        """
        array: T_sheet = []
        for row_idx in range(self.cell_indices.shape[0]):
            row: List[Cell] = []
            for col_idx in range(self.cell_indices.shape[1]):
                row.append(Cell(row_idx, col_idx,
                                cell_indices=self.cell_indices))
            array.append(row)
        return array

    def _set_item(self,
                  value: T_cell_val,
                  index_integer: Tuple[int, int]) -> None:
        """Set the spreadsheet cell on the desired index to the new value.

        Args:
            value (T_cell_val): New value to be inserted.
            index_integer (Tuple[int, int]): integer index (row, column)
                inside spreadsheet (indexed from 0).
        """
        _x, _y = index_integer
        if abs(_x - int(_x)) > 0.000_001 or abs(_y - int(_y)) > 0.000_001:
            raise IndexError("Indices must be integers!")
        # Set values
        if isinstance(value, Cell):
            if value.anchored:
                _value = Cell.reference(value)
            else:
                # Create a deep copy
                _value = copy.deepcopy(value)
                # Anchor it:
                _value.coordinates = (_x, _y)
        else:
            _value = Cell(_x, _y,
                          value=value, cell_indices=self.cell_indices)
        self._sheet[_x][_y] = _value

    def _get_item(self,
                  index_integer: Tuple[int, int]) -> Cell:
        """Get the cell on the particular index.

        Args:
            index_integer (Tuple[int, int]): integer index (row, column)
                inside spreadsheet (indexed from 0).

        Returns:
            Cell: The Cell on the desired index.
        """
        _x, _y = index_integer
        if abs(_x - int(_x)) > 0.000_001 or abs(_y - int(_y)) > 0.000_001:
            raise IndexError("Indices must be integers!")
        return self._sheet[int(_x)][int(_y)]

    def _get_slice(
            self,
            index_integer: Tuple[int, int, int, int, int, int]) -> CellSlice:
        """Get the values in the slice.

        Args:
            index_integer (Tuple[int, int, int, int, int, int]):
                Position of the slice inside array. Indices are 1) row start,
                2) row end (exclusive), 3) row step, 4) column start,
                5) column end (exclusive), 6) column step

        Returns:
            CellSlice: Slice of the cells (aggregate).
        """
        # Receive indices
        _x_start, _x_end, _x_step, _y_start, _y_end, _y_step = index_integer
        # Create the CellSlice object
        cell_subset = []
        for x in range(_x_start, _x_end, _x_step):
            for y in range(_y_start, _y_end, _y_step):
                cell_subset.append(self.iloc[x, y])
        cell_slice: CellSlice = CellSlice((_x_start, _y_start),
                                          (_x_end - 1, _y_end - 1),
                                          cell_subset,
                                          self)
        return cell_slice

    def _set_slice(
            self,
            value: T_cell_val,
            index_integer: Tuple[int, int, int, int, int, int]) -> None:
        """Set the value of each cell in the slice

        Args:
            value (T_cell_val): New value to be set.
            index_integer (Tuple[int, int, int, int, int, int]):
                Position of the slice inside array. Indices are 1) row start,
                2) row end (exclusive), 3) row step, 4) column start,
                5) column end (exclusive), 6) column step
        """
        cell_slice: CellSlice = self._get_slice(index_integer)
        cell_slice.set(value)

    def expand(self,
               new_number_of_rows: int,
               new_number_of_columns: int,
               new_rows_columns: Optional[T_lg_col_row] = {},
               /, *,  # noqa E225
               new_rows_labels: List[str] = None,
               new_columns_labels: List[str] = None,
               new_rows_help_text: List[str] = None,
               new_columns_help_text: List[str] = None
               ):
        """Expand the size of the table.

        Args:
            new_number_of_rows (int): Number of rows to be added.
            new_number_of_columns (int): Number of columns to be added.
            new_rows_columns (T_lg_col_row): List of all row names and column
                names for each language to be added.
            new_rows_labels (List[str]): List of masks (aliases) for row
                names to be added.
            new_columns_labels (List[str]): List of masks (aliases) for
                column names to be added.
            new_rows_help_text (List[str]): List of help texts for each row to
                be added.
            new_columns_help_text (List[str]): List of help texts for each
                column to be added.
        """
        self.expand_using_cell_indices(
            self.cell_indices.expand_size(
                new_number_of_rows,
                new_number_of_columns,
                new_rows_columns,

                new_rows_labels=new_rows_labels,
                new_columns_labels=new_columns_labels,
                new_rows_help_text=new_rows_help_text,
                new_columns_help_text=new_columns_help_text
            )
        )

    def delete_row(self, *,
                   row_index: int = None,
                   row_label: str = None) -> None:
        """Delete the row on given position.

        Args:
            row_index (int): Integer position (indexed from 0).
            row_label (str): Label (string).

        Raises:
            AttributeError: In the case that both type of indices are set.
            IndexError: In the case that index is out of bounds.
        """

        if row_index is not None and row_label is not None:
            raise AttributeError("Only one parameter 'row_index' or "
                                 "'row_label' can be set.")
        if row_label is not None:
            # Find the integer position of the label between indices
            row_index = self.index.index(row_label)

        if row_index is not None:
            if not(0 <= row_index < self.shape[0]):
                raise IndexError("Index is out of bounds!")

            for col_idx in self.shape[1]:
                # Perform the delete operation
                self.iloc[row_index, col_idx].delete(row_index=row_index,
                                                     column_index=col_idx)

    def delete_column(self, *,
                      column_index: int = None,
                      column_label: str = None) -> None:
        """TODO"""
        pass  # TODO

    def insert_row_after(self, *,
                         label: str = None,
                         help_text: str = None,
                         reference_index: int = None,
                         reference_label: str = None) -> None:
        """TODO"""
        if reference_index is not None and reference_label is not None:
            raise IndexError("Only one value 'reference_index' or "
                             "'reference_label' can be set!")
        if reference_label is not None:
            reference_index = self.index.index(reference_label)
        self.insert_row_before(label=label,
                               help_text=help_text,
                               reference_index=reference_index-1)

    def insert_row_before(self, *,
                          label: str = None,
                          help_text: str = None,
                          reference_index: int = None,
                          reference_label: str = None) -> None:
        """TODO"""
        if reference_index is not None and reference_label is not None:
            raise IndexError("Only one value 'reference_index' or "
                             "'reference_label' can be set!")
        pass  # TODO

    def insert_column_after(self, *,
                            label: str = None,
                            help_text: str = None,
                            reference_index: int = None,
                            reference_label: str = None) -> None:
        """TODO"""
        if reference_index is not None and reference_label is not None:
            raise IndexError("Only one value 'reference_index' or "
                             "'reference_label' can be set!")
        if reference_label is not None:
            reference_index = self.columns.index(reference_label)
        self.insert_column_before(label=label,
                                  help_text=help_text,
                                  reference_index=reference_index - 1)

    def insert_column_before(self, *,
                             label: str = None,
                             help_text: str = None,
                             reference_index: int = None,
                             reference_label: str = None) -> None:
        """TODO"""
        if reference_index is not None and reference_label is not None:
            raise IndexError("Only one value 'reference_index' or "
                             "'reference_label' can be set!")
        pass  # TODO

    def _delete_single_cell(self, integer_position: Tuple[int, int]) -> None:
        """Safely delete single cell

        Args:
            integer_position (Tuple[int, int]): Position of the cell in the
                sheet grid (indexed from 0). First is row, second column.
        TODO:
            check if it works
        """
        # Delete value in the cell
        self.iloc[integer_position] = Cell(*integer_position,
                                           cell_indices=self.cell_indices)
        # Delete reference to the cell in all other cells
        for row in range(self.shape[0]):
            for col in range(self.shape[1]):
                if (row, col) == integer_position:
                    continue
                set_to_update = \
                    self.iloc[row, col].update_after_cell_delete(
                        row_index=integer_position[0],
                        column_index=integer_position[1]
                    )
                # Update all cells:
                for index_to_update in set_to_update:
                    self.iloc[index_to_update].re_evaluate(self)

    def _delete_cell_slice(
            self,
            index_integer: Tuple[int, int, int, int, int, int]) -> None:
        """Safely delete cell slice

        Args:
            index_integer (Tuple[int, int, int, int, int, int]):
                Position of the slice inside array. Indices are 1) row start,
                2) row end (exclusive), 3) row step, 4) column start,
                5) column end (exclusive), 6) column step
        """
        print(f"DELETE {index_integer}")

    def expand_using_cell_indices(self, cell_indices: CellIndices) -> None:
        """Resize the spreadsheet object to the greater size

        Args:
            cell_indices (CellIndices): The definition of the shape and columns
                and rows labels, help texts and descriptors.
        """
        shape_origin = self.shape
        self._cell_indices = copy.deepcopy(cell_indices)
        for row_idx in range(self.shape[0]):
            if row_idx >= shape_origin[0]:
                # Append wholly new rows
                row: List[Cell] = []
                for col in range(self.cell_indices.shape[1]):
                    row.append(Cell(cell_indices=self.cell_indices))
                self._sheet.append(row)
            else:
                # Expand columns:
                for col in range(self.cell_indices.shape[1] - shape_origin[1]):
                    self._sheet[row_idx].append(
                        Cell(cell_indices=self.cell_indices)
                    )
            for col_idx in range(self.shape[1]):
                # Has to refresh cell indices everywhere inside
                self.iloc[row_idx,
                          col_idx].cell_indices = self.cell_indices

    # ==== OVERRIDE ABSTRACT METHODS AND PROPERTIES OF SERIALIZATION CLASS ====
    @Serialization.shape.getter
    def shape(self) -> Tuple[int, int]:
        """Return the shape of the sheet in the NumPy logic.

        Returns:
            Tuple[int]: Number of rows, Number of columns
        """
        return self.cell_indices.shape

    @Serialization.cell_indices.getter
    def cell_indices(self) -> CellIndices:
        """Get the cell indices.

        Returns:
            CellIndices: Cell indices of the spreadsheet.
        """
        return self._cell_indices

    def _get_cell_at(self, row: int, column: int) -> 'Cell':
        """Get the particular cell on the (row, column) position.

        Returns:
            Cell: The call on given position.
        """
        return self.iloc[row, column]

    def _get_variables(self) -> '_SheetVariables':
        """Return the sheet variables as _SheetVariables object.

        Returns:
            _SheetVariables: Sheet variables.
        """
        return self.var
    # =========================================================================
