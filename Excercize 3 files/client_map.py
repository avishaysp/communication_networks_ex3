from consts import MAP_PATH


class MapReader:
    def __init__(self, map_file):
        self.matrix = self._load_map(map_file)

    def _load_map(self, map_file):
        matrix = []
        with open(map_file, 'r') as f:
            for line in f:
                strip_line =  line.strip()
                matrix.append([self.__convert_char(c) for c in strip_line])
        return matrix
    
    def get_map(self):
        return self.matrix
    
    def __convert_char(self, char):
        if char == 'W':
            return '█'
        if char == 'F':
            return ' '
        if char == 'P':
            return '·'
        if char == 'S':
            return '∩'
        return char
    
class MapConverter:
    def convert_to_string(self, map_matrix):
        return '\n'.join([''.join(row) for row in map_matrix])
    
if __name__ == '__main__':
    map_reader = MapReader(MAP_PATH)
    map_converter = MapConverter()
    print(map_converter.convert_to_string(map_reader.get_map()))