import sys
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options

def find_best_available_slot(result, current_booking_datetime):
    try:
        # Extract time slots from the result
        time_slots = result.get('ajaxresult', {}).get('slots', {}).get('listTimeSlot', [])
        
        # Define the date range for filtering (May 18, 2025 to June 8, 2025)
        date_range_start = datetime(2025, 5, 18)
        date_range_end = datetime(2025, 6, 8)
        
        # Filter for available slots between 09:59 and 14:01
        # and within the specified date range and before current booking
        filtered_slots = []
        for slot in time_slots:
            if slot.get('availability', True):
                try:
                    slot_datetime = datetime.strptime(slot.get('startTime', ''), "%d/%m/%Y %H:%M")
                    
                    # Check if the slot is within the desired time range
                    slot_time = slot_datetime.time()
                    if slot_time.hour >= 10 and slot_time.hour <= 14:
                        # If it's exactly 14, make sure minutes are 1 or below
                        if slot_time.hour == 14 and slot_time.minute >= 1:
                            continue
                            
                        # Check if the slot is within the date range
                        if date_range_start <= slot_datetime <= date_range_end:
                            
                            # Check if the slot is before the current booking time (if exists)
                            if settings['have_booking'] and current_booking_datetime:
                                # Allow Saturday slots even if they're after current booking
                                is_saturday = slot_datetime.weekday() == 5
                                if slot_datetime >= current_booking_datetime and not is_saturday:
                                    continue
                            
                            slot['slot_datetime'] = slot_datetime
                            filtered_slots.append(slot)
                except ValueError:
                    # Skip slots with invalid datetime format
                    continue
        
        if not filtered_slots:
            return {"message": "No available slots found with the required criteria.", "slot": None}
        
        # Sort filtered slots by date and time
        filtered_slots.sort(key=lambda x: x['slot_datetime'])
        
        # Look for Saturday slots (weekday 5)
        saturday_slots = [slot for slot in filtered_slots if slot['slot_datetime'].weekday() == 5]
        
        if saturday_slots:
            # Return the earliest Saturday slot
            earliest_saturday = saturday_slots[0]
            return {"message": f"Earliest Saturday slot: {earliest_saturday['startTime']}", "slot": earliest_saturday}
        else:
            # Return the earliest available slot if no Saturday slots are found
            earliest_slot = filtered_slots[0]
            return {"message": f"Earliest available slot: {earliest_slot['startTime']}", "slot": earliest_slot}
    except Exception as e:
        return {"message": f"Error processing time slots: {str(e)}", "slot": None}


while True:
    settings = json.load(open("settings.json"))
    chrome_options = Options()
    if(settings['headless']):
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    chrome_options.add_experimental_option("useAutomationExtension", False) 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
    try:
        driver.get("https://www.myrta.com/wps/portal/extvp/myrta/login/")
        driver.find_element(By.ID,"widget_cardNumber").send_keys(settings['username'])
        driver.find_element(By.ID,"widget_password").send_keys(settings['password'])
        time.sleep(settings['wait_timer'])
        driver.find_element(By.ID,"nextButton").click()
        if(settings['have_booking']):
            time.sleep(settings['wait_timer'])
            # driver.find_element(By.XPATH,'//*[text()="Manage booking"]').click()
            driver.find_element(By.XPATH,'//*[text()="Book test"]').click()
            driver.find_element(By.XPATH,'//*[text()="Manage my tests"]').click()
            
            # Extract current booking date and time
            current_booking_date = None
            current_booking_time = None
            try:
                # Find the booking date element
                date_element = driver.find_element(By.XPATH, "//th[contains(text(),'Date of test:')]/following-sibling::td")
                if date_element:
                    current_booking_date = date_element.text.strip()
                    print(f"Current booking date: {current_booking_date}")
                
                # Find the booking time element
                time_element = driver.find_element(By.XPATH, "//th[contains(text(),'Time of test:')]/following-sibling::td")
                if time_element:
                    current_booking_time = time_element.text.strip()
                    print(f"Current booking time: {current_booking_time}")
                    
                # Parse the date and time to create a datetime object
                if current_booking_date and current_booking_time:
                    # Format: "Tuesday, 01 July 2025" and "02:30 PM"
                    date_parts = current_booking_date.split(", ")[1].split(" ")
                    day = date_parts[0]
                    month = date_parts[1]
                    year = date_parts[2]
                    
                    # Convert month name to month number
                    from datetime import datetime
                    month_num = datetime.strptime(month, "%B").month
                    
                    # Parse the time
                    time_obj = datetime.strptime(current_booking_time, "%I:%M %p")
                    hour = time_obj.hour
                    minute = time_obj.minute
                    
                    # Create the full datetime object
                    current_booking_datetime = datetime(int(year), month_num, int(day), hour, minute)
                    print(f"Parsed current booking datetime: {current_booking_datetime}")
            except Exception as e:
                print(f"Error extracting current booking details: {str(e)}")
                current_booking_datetime = None
            
            driver.find_element(By.ID,"changeLocationButton").click()
            time.sleep(settings['wait_timer'])
        else:
            driver.find_element(By.XPATH,'//*[text()="Book test"]').click()
            driver.find_element(By.ID,"CAR").click()
            time.sleep(settings['wait_timer_car'])
            driver.find_element(By.XPATH,"//fieldset[@id='DC']/span[contains(@class, 'rms_testItemResult')]").click()
            time.sleep(settings['wait_timer'])
            driver.find_element(By.ID,"nextButton").click()
            time.sleep(settings['wait_timer'])
            driver.find_element(By.ID,"checkTerms").click()
            time.sleep(settings['wait_timer'])
            driver.find_element(By.ID,"nextButton").click()
            time.sleep(settings['wait_timer'])
            driver.find_element(By.ID,"rms_batLocLocSel").click()
            time.sleep(settings['wait_timer'])
        driver.find_element(By.ID,"rms_batLocLocSel").click()
        time.sleep(settings['wait_timer'])
        select_box = driver.find_element(By.ID,"rms_batLocationSelect2")
        Select(select_box).select_by_value(sys.argv[1])
            
        # Set up variables for the location search loop
        max_attempts = 1000  # Maximum number of location attempts
        current_attempt = 0
        best_slot = None
        best_slot_info = "No suitable slot found"
        
        while current_attempt < max_attempts and not best_slot:
            time.sleep(settings['wait_timer_car'])
            driver.find_element(By.ID,"nextButton").click()

            current_attempt += 1
            print(f"Attempt {current_attempt} of {max_attempts} to find a suitable slot")
            
            # Initialize result structure
            result = {
                "ajaxresult": {
                    "slots": {
                        "listTimeSlot": []
                    }
                }
            }

            time.sleep(settings['wait_timer_car'])
            if(driver.find_element(By.ID,"getEarliestTime").size!=0):
                if(driver.find_element(By.ID,"getEarliestTime").is_displayed()):
                    if(driver.find_element(By.ID,"getEarliestTime").is_enabled()):
                        driver.find_element(By.ID,"getEarliestTime").click()
                        # Add the updated timeslots to the result, not replace it
                        updated_result = driver.execute_script('return timeslots')
                        if updated_result and 'ajaxresult' in updated_result and 'slots' in updated_result['ajaxresult'] and 'listTimeSlot' in updated_result['ajaxresult']['slots']:
                            # Combine the time slots from both results
                            if 'ajaxresult' not in result:
                                result['ajaxresult'] = {}
                            if 'slots' not in result['ajaxresult']:
                                result['ajaxresult']['slots'] = {}
                            if 'listTimeSlot' not in result['ajaxresult']['slots']:
                                result['ajaxresult']['slots']['listTimeSlot'] = []
                            
                            # Add new time slots from updated_result to result
                            result['ajaxresult']['slots']['listTimeSlot'].extend(updated_result['ajaxresult']['slots']['listTimeSlot'])
                            
                            # Remove duplicates based on startTime
                            seen_start_times = {}
                            unique_time_slots = []
                            
                            for slot in result['ajaxresult']['slots']['listTimeSlot']:
                                start_time = slot.get('startTime')
                                if start_time and start_time not in seen_start_times:
                                    seen_start_times[start_time] = True
                                    unique_time_slots.append(slot)
                            
                            # Update the result with the combined unique time slots
                            result['ajaxresult']['slots']['listTimeSlot'] = unique_time_slots
            
            time.sleep(settings['wait_timer'])
            
            # Find the best available slot
            best_slot_result = find_best_available_slot(result, current_booking_datetime)
            best_slot_info = best_slot_result["message"]
            best_slot = best_slot_result["slot"]
            
            # If no best slot found and we haven't reached max attempts, try a different location
            if not best_slot and current_attempt < max_attempts:
                print("No suitable slot found. Trying a different location...")
                try:
                    # Click on "Try a different location" link
                    different_location_link = driver.find_element(
                        By.XPATH, 
                        "//a[contains(@href, \"javascript:navToView('chooseLocation')\")]"
                    )
                    different_location_link.click()
                    # time.sleep(settings['wait_timer'])
                    
                    # # Select location again
                    # select_box = driver.find_element(By.ID,"rms_batLocationSelect2")
                    # Select(select_box).select_by_value(sys.argv[1])
                    # time.sleep(settings['wait_timer'])
                    
                    # # Click next to search for times
                    # driver.find_element(By.ID,"nextButton").click()
                    # time.sleep(settings['wait_timer'])
                except Exception as e:
                    print(f"Error trying different location: {str(e)}")
                    break
            else:
                # Either we found a suitable slot or reached max attempts
                break
        
        # Log the outcome of our search
        if best_slot:
            print(f"Found suitable slot after {current_attempt} attempts: {best_slot_info}")
        else:
            print(f"Failed to find suitable slot after {current_attempt} attempts")
        
        # Try to click on the selected time slot if found
        if best_slot:
            try:
                # Extract time information from the slot
                slot_datetime = datetime.strptime(best_slot['startTime'], "%d/%m/%Y %H:%M")
                hour = slot_datetime.hour
                minute = slot_datetime.minute
                
                # Format time for UI element identifier (e.g., "2:00 pm")
                hour_12 = hour % 12
                if hour_12 == 0:
                    hour_12 = 12
                am_pm = "am" if hour < 12 else "pm"
                time_text = f"{hour_12}:{minute:02d} {am_pm}"
                
                # Try different approaches to find and click the button
                # Method 1: Find by exact matching a element with class 'available'
                # try:
                #     time_button = driver.find_element(By.XPATH, f"//a[@class='available' and text()='{time_text}']")
                #     time_button.click()
                #     print(f"Clicked on time slot: {time_text}")
                # except:
                try:
                    # Method 2: Find the td element and click its a child
                    prefix = "rms_mon" if slot_datetime.weekday() == 0 else \
                                "rms_tue" if slot_datetime.weekday() == 1 else \
                                "rms_wed" if slot_datetime.weekday() == 2 else \
                                "rms_thu" if slot_datetime.weekday() == 3 else \
                                "rms_fri" if slot_datetime.weekday() == 4 else \
                                "rms_sat" if slot_datetime.weekday() == 5 else "rms_sun"
                    
                    # Format hour for element ID (e.g., "rms_mon_200" for 2:00)
                    hour_id = f"{hour_12}{minute:02d}"
                    td_id = f"{prefix}_{hour_id}"
                    
                    time_cell = driver.find_element(By.ID, td_id)
                    link = time_cell.find_element(By.TAG_NAME, "a")
                    link.click()
                    print(f"Clicked on time slot using td ID: {td_id}")
                # except:
                    # Method 3: Try with contains
                    # try:
                    #     time_button = driver.find_element(By.XPATH, f"//a[contains(@class, 'available') and contains(text(), '{time_text}')]")
                    #     time_button.click()
                    #     print(f"Clicked on time slot using contains: {time_text}")
                except Exception as click_error:
                    print(f"Could not click on time slot: {time_text}. Error: {str(click_error)}")
                

                driver.find_element(By.ID,"nextButton").click()
                # Try to find and click the next button if it exists
                # try:
                #     next_button = driver.find_element(By.ID, "nextButton")
                #     if next_button.is_displayed() and next_button.is_enabled():
                #         next_button.click()
                #         print("Clicked next button after selecting time slot")
                #         time.sleep(settings['wait_timer'])
                # except Exception as next_error:
                #     print(f"Could not click next button: {str(next_error)}")

                time.sleep(settings['wait_timer'])    
                # Find and click the checkbox by its ID instead of clicking on the text
                driver.find_element(By.ID, "checkTerms").click()
                driver.find_element(By.ID,"nextButton").click()

            except Exception as e:
                print(f"Error clicking on time slot: {str(e)}")
        


        # Write results to file
        # results_file = open(sys.argv[2], "a")
        # results_file.write(f'{{"location":"{sys.argv[1]}","result":{json.dumps(result)},"best_slot":"{best_slot_info}"}}\n')
        # results_file.close()
        
        driver.quit()
    except Exception as e:
        print(f"Error: {str(e)}")
        driver.quit()
        # exit(1)