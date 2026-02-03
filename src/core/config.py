# Configuration constants for the Earthworm application

# Column names used in the DataFrame
DEPTH_COLUMN = 'DEPT'
LITHOLOGY_COLUMN = 'LITHOLOGY_CODE' # Column for classified lithology (old name, maintained for backward compatibility)
LITHOQUAL_COLUMN = 'LITHO_QUALITY' # Placeholder for original lithology quality if present
LITHOLOGY_QUAL_COLUMN = 'LITHOLOGY_QUALITY_COMBINED' # Placeholder for combined lithology and quality

# New 37-column CoalLog v3.1 schema column names
# Primary column names (new schema uses snake_case)
LITHOLOGY_COLUMN_NEW = 'lithology'  # New column name for lithology
RECOVERED_THICKNESS_COLUMN = 'recovered_thickness'  # New column name for thickness
RECORD_SEQUENCE_FLAG_COLUMN = 'record_sequence_flag'  # New column name for record sequence
INTERRELATIONSHIP_COLUMN = 'interrelationship'  # New column name for interrelationship
LITHOLOGY_PERCENT_COLUMN = 'lithology_percent'  # New column name for percentage

# Column mapping for backward compatibility
COLUMN_NAME_MAPPING = {
    # Old column names -> New column names
    'LITHOLOGY_CODE': 'lithology',
    'thickness': 'recovered_thickness',
    'record_sequence': 'record_sequence_flag',
    'inter_relationship': 'interrelationship',
    'percentage': 'lithology_percent',
    # New columns that don't have old equivalents will be added with defaults
}

# Reverse mapping for migration
REVERSE_COLUMN_MAPPING = {v: k for k, v in COLUMN_NAME_MAPPING.items()}

# Complete list of 37 columns in CoalLog v3.1 schema
COALLOG_V31_COLUMNS = [
    # Depth/Thickness (3 columns)
    'from_depth', 'to_depth', 'recovered_thickness',
    # Identification (7 columns)
    'record_sequence_flag', 'seam', 'ply', 'horizon',
    'sample_purpose', 'lithology_sample_number', 'interval_status',
    # Lithology description (12 columns)
    'lithology', 'lithology_qualifier', 'lithology_percent',
    'shade', 'hue', 'colour',
    'adjective_1', 'adjective_2', 'adjective_3', 'adjective_4',
    'interrelationship', 'lithology_descriptor',
    # Geotechnical properties (6 columns)
    'weathering', 'estimated_strength', 'bed_spacing',
    'core_state', 'mechanical_state', 'texture',
    # Structural features (5 columns)
    'defect_type', 'intact', 'defect_spacing', 'defect_dip', 'bedding_dip',
    # Sedimentology (2 columns)
    'basal_contact', 'sedimentary_feature',
    # Mineralogy (2 columns)
    'mineral_fossil', 'abundance'
]

# Default values for new columns when loading old data
DEFAULT_COLUMN_VALUES = {
    'record_sequence_flag': '',
    'seam': '',
    'ply': '',
    'horizon': '',
    'sample_purpose': '',
    'lithology_sample_number': '',
    'interval_status': '',
    'adjective_1': '',
    'adjective_2': '',
    'adjective_3': '',
    'adjective_4': '',
    'lithology_descriptor': '',
    'core_state': '',
    'mechanical_state': '',
    'texture': '',
    'defect_type': '',
    'intact': '',
    'defect_spacing': '',
    'defect_dip': '',
    'bedding_dip': '',
    'basal_contact': '',
    'sedimentary_feature': '',
    'mineral_fossil': '',
    'abundance': ''
}

# Columns used for lithology analysis (e.g., for classification rules)
ANALYSIS_COLUMNS = ['gamma', 'density']

# Default ranges for plotting curves
CURVE_RANGES = {
    'gamma': {'min': 0, 'max': 150, 'color': '#00FF00'}, # Green
    'density': {'min': 1.5, 'max': 3.0, 'color': '#FF0000'}, # Red (assuming this is the primary density, will be replaced by short_space_density if present)
    'short_space_density': {'min': 1.5, 'max': 3.0, 'color': '#FF0000'}, # Red
    'long_space_density': {'min': 1.5, 'max': 3.0, 'color': '#0000FF'} # Blue
}

# Value used to represent invalid or missing data in input files
INVALID_DATA_VALUE = -999.25

# Default lithology classification rules/ranges
# These rules define the criteria for classifying different lithology types
DEFAULT_LITHOLOGY_RULES = [
    {'name': 'Coal', 'code': 'CO', 'gamma_min': 0, 'gamma_max': 20, 'density_min': 0, 'density_max': 1.8, 'background_color': '#000000'},
    {'name': 'Sandstone', 'code': 'SS', 'gamma_min': 21, 'gamma_max': 50, 'density_min': 2.0, 'density_max': 2.7, 'background_color': '#FFFF00'},
    {'name': 'Shale', 'code': 'SH', 'gamma_min': 51, 'gamma_max': 100, 'density_min': 2.5, 'density_max': 3.0, 'background_color': '#A9A9A9'},
    {'name': 'Not Logged', 'code': 'NL', 'gamma_min': -1, 'gamma_max': -1, 'density_min': -1, 'density_max': -1, 'background_color': '#E0E0E0'}
]

# Well-researched default ranges for common lithologies when user-defined ranges are missing or zero
# These are general guidelines and may need adjustment based on specific geological contexts.
# Users are encouraged to verify these ranges with their own data or scientific literature.
RESEARCHED_LITHOLOGY_DEFAULTS = {
    'CO': {'gamma_min': 0, 'gamma_max': 20, 'density_min': 1.2, 'density_max': 1.8}, # Coal
    'SS': {'gamma_min': 20, 'gamma_max': 60, 'density_min': 2.4, 'density_max': 2.7}, # Sandstone
    'ST': {'gamma_min': 50, 'gamma_max': 100, 'density_min': 2.2, 'density_max': 2.6}, # Siltstone
    'SH': {'gamma_min': 80, 'gamma_max': 150, 'density_min': 2.5, 'density_max': 2.8}, # Shale
    'XM': {'gamma_min': 60, 'gamma_max': 120, 'density_min': 2.0, 'density_max': 2.3}, # Carbonaceous Mudstone (example range)
    'ZM': {'gamma_min': 30, 'gamma_max': 80, 'density_min': 1.7, 'density_max': 2.1}  # Coaly Mudstone (example range)
}

# Stratigraphic Column Visual Settings
DEFAULT_SEPARATOR_THICKNESS = 0.5 # Default thickness for separator lines in the stratigraphic column
DRAW_SEPARATOR_LINES = True # Whether to draw separator lines in the stratigraphic column by default

# Default inversion settings for curves
CURVE_INVERSION_DEFAULTS = {
    'gamma': False,
    'short_space_density': False,
    'long_space_density': False
}

# Default curve line thickness
DEFAULT_CURVE_THICKNESS = 1.5 # Default thickness for curve lines

# Thin unit merging settings
DEFAULT_MERGE_THIN_UNITS = False # Whether to merge thin units by default
DEFAULT_MERGE_THRESHOLD = 0.05 # 5cm in meters - threshold for merging thin units

# Smart interbedding settings
DEFAULT_SMART_INTERBEDDING = False # Whether to enable smart interbedding by default
DEFAULT_SMART_INTERBEDDING_MAX_SEQUENCE_LENGTH = 10 # Maximum segments in interbedded sequence before stopping
DEFAULT_SMART_INTERBEDDING_THICK_UNIT_THRESHOLD = 0.5 # Stop interbedding when next unit exceeds this thickness (meters)
DEFAULT_FALLBACK_CLASSIFICATION = False # Whether to enable fallback classification to reduce "NL" results
