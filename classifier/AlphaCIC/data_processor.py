import json
class DataProcessor:
    def __init__(self, data, from_json=False):
        """
        Data must be in the form of a list of tuples or a dictionary loaded from JSON,
        where each tuple or dictionary entry is a datapoint.
        
        If the input data is a dictionary (loaded from JSON), it will be automatically
        converted to the required format of a list of tuples.
        
        The keys of the dictionary must be the following:
            - 'SECTION': a string with the title of the section in which the citation is found
            - 'CITATION': a string representing the citation text itself
        
        Please, pay attention to the following:
            - If 'SECTION' is not present, replace it with an empty string ("", no space in between)
            - If 'CITATION' is not present, the datapoint will be ignored
        """
        self.from_json = from_json
        if self.from_json:
            self.raw_data = data
            self.data = self.check_json(self.raw_data)
        else:
            self.data = self.check_data(data)
            self.data_length = len(self.data)
            self.ids = self.generate_ids()
            self.mapped_data = self.generate_mapping()

    def check_json(self, data):
        """
        Check that each datapoint has the required keys.
        """
        configured_data = {}
        for id in data:
            if data[id]['CITATION'] == "":
                pass
            else:
                configured_data[id] = {
                    'SECTION': data[id]['SECTION'],
                    'CITATION': data[id]['CITATION']
                }
        return configured_data

    def check_data(self, data):
        """
        Check that each datapoint has the required keys.
        """
        configured_data = []
        for datapoint in data:
            if datapoint[1] == "":
                pass
            else:
                configured_data.append(
                    {
                        'SECTION': datapoint[0],
                        'CITATION': datapoint[1]
                    }
                )
        return configured_data

    def generate_ids(self):
        """
        Generate a list of ids for each datapoint.
        """
        ids = list(range(self.data_length))
        return ids
    
    def generate_mapping(self):
        """
        Maps each datapoint to a specific id.
        """
        mapped_data = dict(zip(self.ids, self.data))
        """
        MAPPED DATA FORMAT:
        {
            1: {
                'SECTION': 'Introduction',
                'CITATION': 'This is a citation'
            },
            2: {
                'SECTION': 'Introduction',
                'CITATION': 'This is another citation'
            },
            ...
        }
        """
        return mapped_data
    
def read_json(json_file):
    try:
        data = json.load(json_file)
        simple_format_check = True
        for id in data:
            if len(data[id]) > 2:
                simple_format_check = False
            elif len(data[id]) == 2:
                pass
            else:
                raise ValueError("Invalid JSON file, the number of keys is not correct. The keys must be at least 'SECTION' and 'CITATION' in each entry.")
            if 'SECTION' not in data[id] or 'CITATION' not in data[id]:
                raise ValueError("Invalid JSON file, not all the necessary keys are present. At least 'SECTION' and 'CITATION' must be present in each entry.")
        
        if simple_format_check:
            return data
        else:
            if not simple_format_check:
                clean_data = {}
                temporary_data = data
                for id in data:
                    clean_data[id] = {}
                    clean_data[id]['SECTION'] = data[id]['SECTION']
                    clean_data[id]['CITATION'] = data[id]['CITATION']
                return (clean_data, temporary_data)
        print("Data loaded from JSON:", data)
        return data
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON file")


#USAGE EXAMPLE:
"""
data = [
("Literature Review", "In their comprehensive review, Smith and colleagues (2019) delineate the historical development of nanomaterials in modern applications."),
("", "The foundational work by Doe et al. (2015) establishes the prevailing theoretical framework guiding current research paradigms."),
("Research Methodology", "Our process analysis technique was adopted from the methodology proposed by Johnson et al. (2018) in their study on efficient data algorithms."),
("Experimental Procedures", ""),
("Findings and Analysis", "Consistent with the observations reported by Lee and Khan (2020), our results indicate a significant correlation between sunlight exposure and the rate of photosynthesis."),
("Discussion", "Contrary to the predictions made by Fujiwara's model (2016), our experiment did not observe a steady quantum coherence under thermal fluctuations.")
]
processor = DataProcessor(data)
print(processor.mapped_data)
"""