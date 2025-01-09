from enum import Enum
from consts import MAP_PATH


class WorldMap:
    class Entry(Enum):
        WALL =  '█'
        FLOOR = ' '
        POINT = '·'
        CMAN =  'C'
        GHOST = '∩'

    def __init__(self, map_file):
        self.matrix = self._load_map(map_file)
        self.__starting_points_indexes = self.__get_point_indexes()
        self.current_cman_idx = self.__get_cman_index()
        self.current_ghost_idx = self.__get_ghost_index()

    def _load_map(self, map_file):
        matrix = []
        with open(map_file, 'r') as f:
            for line in f:
                strip_line =  line.strip()
                matrix.append([self.__convert_char(c) for c in strip_line])
        return matrix
    
    def __get_point_indexes(self):
        point_indexes = []
        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                if val == WorldMap.Entry.POINT.value:
                    point_indexes.append((i, j))
        return point_indexes
    
    def __get_cman_index(self):
        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                if val == WorldMap.Entry.CMAN.value:
                    return (i, j)
        print(self.to_string())
        assert False, 'Cman not found'
    
    def __get_ghost_index(self):
        for i, row in enumerate(self.matrix):
            for j, val in enumerate(row):
                if val == WorldMap.Entry.GHOST.value:
                    return (i, j)

        print(self.to_string())
        assert False, 'Ghost not found'
    
    def get_starting_points_indexes(self):
        return self.__starting_points_indexes
    
    def to_string(self):
        return '\n'.join([''.join(row) for row in self.matrix])
    
    def __convert_char(self, char):
        if char == 'W':
            return WorldMap.Entry.WALL.value
        if char == 'F':
            return WorldMap.Entry.FLOOR.value
        if char == 'P':
            return WorldMap.Entry.POINT.value
        if char == 'S':
            return WorldMap.Entry.GHOST.value
        return char
    
    def get(self, row, col):
        return self.matrix[row][col]
    
    def remove_players(self):
        self.matrix[self.current_cman_idx[0]][self.current_cman_idx[1]] = WorldMap.Entry.FLOOR.value
        self.matrix[self.current_ghost_idx[0]][self.current_ghost_idx[1]] = WorldMap.Entry.FLOOR.value
    
    def remove_point(self, row, col):
        self.matrix[row][col] = ' '
    
    def place_point(self, row, col):
        self.matrix[row][col] = '·'
    
    def place_cman(self, row, col):
        self.matrix[row][col] = WorldMap.Entry.CMAN.value
        self.current_cman_idx = (row, col)

    def place_ghost(self, row, col):
        self.matrix[row][col] = WorldMap.Entry.GHOST.value
        self.current_ghost_idx = (row, col)
    
if __name__ == '__main__':
    map_reader = WorldMap(MAP_PATH)
    print(map_reader.to_string())