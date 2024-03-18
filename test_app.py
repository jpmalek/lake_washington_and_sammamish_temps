import pytest
"""
 NOTE: to run unit tests and generate a coverage report in the htmlcov directory:  
           pytest test_app.py --cov=app --cov-report html
"""
# @pytest.fixture
# def mocker_file_manager(mocker):
#     mock_boto3_client = mocker.patch('boto3.client')
#     mock_client = mock_boto3_client.return_value
#     from app import FileManager
#     # To set return values for specific client methods, do so here.
#     # For example, if FileManager uses the 'get_object' method of an S3 client:
#     # mock_client.get_object.return_value = {
#     #     'Body': 'mock body',
#     #     # Add other keys as needed
#     # }
#     return mocker.Mock(spec=FileManager)

# @pytest.fixture
# def mocker_chrome_utility(mocker):
#     from app import ChromeUtility
#     return mocker.Mock(spec=ChromeUtility)

# @pytest.fixture
# def mocker_process_data(mocker):
#     from app import ProcessData
#     return mocker.Mock(spec=ProcessData)

# @pytest.fixture
# def mocker_king_county_lakes(mocker):
#     from app import KingCountyLakes
#     return mocker.Mock(spec=KingCountyLakes)

# def test_file_manager_init(mocker_file_manager):
#     # Call the method
#     mocker_file_manager()
#     # Assert that the method was called
#     mocker_file_manager.assert_called()

# def test_file_manager_backup_file(mocker_file_manager):
#     # Call the method
#     mocker_file_manager.backup_file('test_file')
#     # Assert that the method was called with the correct arguments
#     mocker_file_manager.backup_file.assert_called_with('test_file')

# def test_chrome_utility_get_historical_wa_lake_data_locations(mocker_chrome_utility):
#     # Call the method
#     mocker_chrome_utility.get_historical_wa_lake_data_locations()
#     # Assert that the method was called
#     mocker_chrome_utility.get_historical_wa_lake_data_locations.assert_called()

# def test_process_data_high_and_low_temps(mocker_process_data):
#     # Call the method with some test data
#     mocker_process_data.high_and_low_temps([{'temp': 10}, {'temp': 20}, {'temp': 30}])
#     # Assert that the method was called with the correct arguments
#     mocker_process_data.high_and_low_temps.assert_called_with([{'temp': 10}, {'temp': 20}, {'temp': 30}])
#     # TODO: use mock data to test monthly, all time high and low temps

# def test_king_county_lakes_get_all_historical_wa_lake_data(mocker_king_county_lakes):
#     # Call the method
#     mocker_king_county_lakes.get_all_historical_wa_lake_data()
#     # Assert that the method was called
#     mocker_king_county_lakes.get_all_historical_wa_lake_data.assert_called()

def test_chrome_utility_get_historical_wa_lake_data_locations():
    from app import ChromeUtility
    cu = ChromeUtility()
    locations = cu.get_historical_wa_lake_data_locations()
    
    
