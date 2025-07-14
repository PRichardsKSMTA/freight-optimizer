import pandas

from file_manager import FileManager

def read_csv_with_log(
                    filename: str,
                    file_manager: FileManager,
                    unique_columns: iter=[],
                    required_columns: iter=None,
                    identifier: str='',
                    file_is_required: bool=True,
                    copy_to_output: bool=False
                    ) -> pandas.DataFrame:
    '''
    reads a .csv file and verifies that all fields in the iterable required_columns are included.
        filename: a .csv filename - this should include the directory for the file
        required_columns: an iterable of the column names that are required in the input csv file
        identifier: a string identifier for this filename - this will be used for logging
        unique_columns: a list of column names that must have unique row values (e.g. vessel_call_id). This
            will throw an error if any values are not unique.
        file_is_required: a boolean indicating whether the file is required. If True, an error will be thrown
            if the file is not found. If False, a warning will be logged if the file is not found.
        copy_to_output: a boolean indicating whether to copy the input file to the output folder.
    '''
    try:
        try:
            df = pandas.read_csv(file_manager.input_folder + '/' + filename + '.csv')
            if copy_to_output:
                file_manager.write_input_to_output(filename + '.csv')
        except:
            try:
                df = pandas.read_excel(file_manager.input_folder + '/' + filename + '.xlsx')
                if copy_to_output:
                    file_manager.write_input_to_output(filename + '.xlsx')
            except:
                try:
                    df = pandas.read_excel(file_manager.input_folder + '/' + filename + '.xls')
                    if copy_to_output:
                        file_manager.write_input_to_output(filename + '.xls')
                except:
                    df = pandas.read_csv(file_manager.input_folder + '/' + filename + '.txt', sep='\t')
                    if copy_to_output:
                        file_manager.write_input_to_output(filename + '.txt', sep='\t')
        original_df_shape = df.shape[0]
        df = df.dropna(axis = 0, how = 'all')
        new_df_shape = df.shape[0]

        if new_df_shape != original_df_shape:
            message_type = 'warning'
            message = 'Dropped ' + str(int(original_df_shape - new_df_shape)) + ' empty rows from the ' + identifier + ' file.'
            file_manager.add_message_to_log(message, message_type)
    except Exception as ee:
        message_type = 'warning'
        message = 'Unable to read ' + identifier + ' file. The most likely causes of this error are that the file is not in the correct format (comma seperated values, .csv) or the file does not exist in the expected location: ' + str(filename)
        message += '\nThe full exception message is: ' + str(ee)
        if file_is_required:
            message_type = 'error'
        file_manager.add_message_to_log(message, message_type)

        if file_is_required:
            raise ValueError(message)
        else:
            return pandas.DataFrame()

    if not required_columns is None:
        field_name_validator(df, required_columns, identifier=identifier, file_manager=file_manager)

    for unique_col in unique_columns:
        if df[unique_col].is_unique:
            continue

        message_type = 'error'
        message = 'The ' + str(unique_col) + ' column in the ' + identifier + ' file must contain all unique values. Please rename or remove duplicates and re-run optimization'
        file_manager.add_message_to_log(message, message_type)
        raise ValueError(message)   		

    return df   


def field_name_validator(df: pandas.DataFrame, required_columns: iter, 
                         identifier: str, file_manager: FileManager) -> None:
    """This function validates that all required fields in the input dataframe are present

    Args:
        df (pandas.DataFrame): The input dataframe to test
        required_columns (iter): An iterable of the required column names for the input dataframe
        identifier (str): An identifier for this dataframe (used for Exception handling)

    Raises:
        ValueError: If any of the required columns are not present in the input dataframe
    """		
    for field in required_columns:
        if not field in df.columns.values:
            message_type = 'error'
            message = 'Required field: ' + field + ' not found in ' + identifier
            file_manager.add_message_to_log(message, message_type)    
            raise ValueError(message)
    
    message_type = 'success'
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    message = 'Table ' + identifier + ' successfully read, with ' + str(num_rows) + 'rows and ' + str(num_cols) + ' columns.'
    file_manager.add_message_to_log(message, message_type)


def read_empty_miles(file_manager: FileManager) -> pandas.DataFrame:
    '''
    Reads the empty miles file and returns a pandas dataframe with the origin_zip, 
    destination_zip, empty_miles, and empty_cost columns.

    Args:
        file_manager (FileManager): The file manager object

    Returns:
        pandas.DataFrame: The empty miles dataframe
    '''
    required_columns = [file_manager.params['data']['empty_miles']['columns'][x[0]] for x \
                    in file_manager.params['data']['empty_miles']['columnRequired'].items() if x[1]]
    empty_miles_df= read_csv_with_log(
            filename=file_manager.params['data']['empty_miles']['filename'],
            identifier='Empty Miles',
            required_columns=required_columns,
            file_manager=file_manager
        )
    empty_miles_df= empty_miles_df.rename({
            file_manager.params['data']['empty_miles']['columns']['origin_zip']: 'origin_zip',
            file_manager.params['data']['empty_miles']['columns']['destination_zip']: 'destination_zip',
            file_manager.params['data']['empty_miles']['columns']['empty_miles']: 'empty_miles',
            file_manager.params['data']['empty_miles']['columns']['empty_cost']: 'empty_cost',
    }, axis=1)
    empty_miles_df['origin_zip'] = empty_miles_df['origin_zip'].apply(lambda x: str(x).zfill(3))
    empty_miles_df['destination_zip'] = empty_miles_df['destination_zip'].apply(lambda x: str(x).zfill(3))
    empty_miles_df['origin_zip'] = empty_miles_df['origin_zip'].apply(lambda x: str(x).ljust(5, '0'))
    empty_miles_df['destination_zip'] = empty_miles_df['destination_zip'].apply(lambda x: str(x).ljust(5, '0'))
    empty_miles_df= empty_miles_df.drop_duplicates(subset=['origin_zip', 'destination_zip'])

    empty_miles_df.set_index(['origin_zip', 'destination_zip'], inplace=True)

    return empty_miles_df