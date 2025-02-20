#import libraries---------------------------------------------------------------------------
import math 
import pandas as pd
from datetime import datetime
from random import shuffle
from copy import deepcopy
#from fpdf import FPDF
import csv

    #file locations
course_file = "MockClasses.csv"
faculty_file = "MockFaculty.csv"
manager_file = "MockManagers.csv"
schedule_file = "Faculty_Courses_Simplified.csv"
schedule_file_long = "Faculty_Courses_Full.csv"
Unassigned_courses = "Unassigned_Courses.csv"

    #constants
manager_weight: float = 0.5
max_hours = 9
iterations  = 5

#main function----------------------------------------------------------------------------
def main() -> None:
    #create a log
    # date = datetime.now()
    # log_name = f"Scheduler_log_{date.strftime("%d%m%Y_%H_%M_%S")}.txt"
    # error_log = open(log_name, "w")
    # del date
        
    #read in course as data dataframe
    extract = pd.read_csv(course_file)
    Courses = list(extract["Course"].unique())
    Campus = list(extract["Campus"].unique())
    Modality = list(extract["Modality"].unique())
    del extract
    
    #create a merged database of faculy and manager preferences
    faculty_extract: pd = pd.read_csv(faculty_file)
    manager_extract: pd = pd.read_csv(manager_file)
    merged_extract = pd.merge(manager_extract, faculty_extract, how = "left", on = ["ID","ID"], suffixes = ["m", "f"], validate = "1:1")
    merged_extract = merged_extract.drop(columns = ["FirstNamem", "LastNamem"])
    merged_extract = merged_extract.rename(columns = {"LastNamef": "Last", "FirstNamef": "First"})
    del faculty_extract
    del manager_extract
                   
    #create dictionaries 
    global Course_dictionary
    Course_dictionary = {}
    for i, course in enumerate(Courses):
        Course_dictionary[course] = i
        
    # global Campus_dictionary
    global Campus_dictionary
    Campus_dictionary = {}
    for i, campus in enumerate(Campus):
        Campus_dictionary[campus] = i        

    # global Modality_dictionary
    global Modality_dictionary
    Modality_dictionary = {}
    for i, mode in enumerate(Modality):
        Modality_dictionary[mode] = i   

   #build courses
    course_list = []
    with open(course_file, 'r') as file:
        reader = csv.reader(file, delimiter = ",")
        for i, line in enumerate(reader):
            if i > 0: #skips header row
                if line[9] == "ON":
                    LecTime = []
                    LecDOW = []
                    LabTime = []
                    LabDOW = []
                elif line[9] == "HY":
                    LecTime = []
                    LecDOW = []
                    LabTime = Course_time_to_array(line[4], line[5])
                    LabDOW = Days_of_week_to_list(line[3])
                elif line[9] == "IN":
                    LecTime = Course_time_to_array(line[7], line[8])
                    LecDOW = Days_of_week_to_list(line[6])
                    LabTime = Course_time_to_array(line[4], line[5])
                    LabDOW = Days_of_week_to_list(line[3]) 
                course_list.append(CourseMaker(line[0], line[1], LecTime, LecDOW, LabTime, LabDOW, int(line[10]), line[2], line[9],[line[7],line[8]],line[6],[line[4],line[5]],line[3]))
    
            #build faculty list 
        
    faculty_list = []
    for i in range(1, len(merged_extract)):
        faculty_list.append(faculty(f"{merged_extract["First"].values[i]} {merged_extract["Last"].values[i]}", get_id(merged_extract["ID"].values[i]), float(merged_extract["Weight"].values[i]), merged_extract["D_pref"].values[i], merged_extract["T_pref"].values[i], merged_extract["C_Preff"].values[i], merged_extract["Camp_preff"].values[i], merged_extract["C_Prefm"].values[i], merged_extract["Camp_prefm"].values[i],merged_extract["Modalityf"].values[i], merged_extract["Modalitym"].values[i])) 
    del merged_extract
    
    #begin to search for optimal class assignments
    
        #create two initial randomized scores
    iteration = 0
    
    faculty_list_1, course_list_1, assigned_courses_1, score_1 = schedule_builder(deepcopy(faculty_list), deepcopy(course_list))
    faculty_list_2, course_list_2, assigned_courses_2, score_2 = schedule_builder(deepcopy(faculty_list), deepcopy(course_list))
    
        #compares random schedules until the 2nd randomly generated schedule doesn't beat the initial randomized schedule three times
    while iteration < iterations:
        print(f"score 1 = {score_1}, score 2 = {score_2}")
        if score_1 > score_2:
            iteration += 1
            del faculty_list_2, course_list_2, assigned_courses_2, score_2
            faculty_list_2, course_list_2, assigned_courses_2, score_2 = schedule_builder(deepcopy(faculty_list), deepcopy(course_list))
        if score_1 < score_2:
            iteration = 0
            del faculty_list_1, course_list_1, assigned_courses_1, score_1
            faculty_list_1 = deepcopy(faculty_list_2)
            course_list_1 = deepcopy(course_list_2)
            assigned_courses_1 = deepcopy(assigned_courses_2)
            score_1 = score_2
            del faculty_list_2, course_list_2, assigned_courses_2, score_2
            faculty_list_2, course_list_2, assigned_courses_2, score_2 = schedule_builder(deepcopy(faculty_list), deepcopy(course_list))
    
    #print out faculty course assignments
    file = open(schedule_file, "w")
    
    for v in faculty_list_1:
        file.write(f"{v.faculty}")
        if len(v.courses) > 0:
            for w in v.courses:
                file.write(f", {w[0]} {w[1]}")
        file.write(f" {v.hours} ")
        file.write("\n")
    file.close()
    
        #print out faculty course assignments with full details
    file = open(schedule_file_long, "w")
    
    file.write("Faculty,Faculty ID,Course Name,Course Section,Modality,Lecture Times,Lecture Days,Lab Times,Lab Days\n")
    for v in faculty_list_1:
        if len(v.courses) == 0:
            file.write(f"{v.faculty},{v.faculty_id},no assigned courses\n")
        else:
            for w in v.courses:
                if w[3] == "ON":
                    file.write(f"{w[0]},{w[1]},{w[3]},NA,NA,NA,NA\n")
                if w[3] == "HY":
                    file.write(f"{w[0]},{w[1]},{w[3]},NA,NA,{w[6][0]} - {w[6][1]},{w[7]}\n")
                else:
                    file.write(f"{w[0]},{w[1]},{w[3]},{w[4][0]} - {w[4][1]},{w[5]},{w[6][0]} - {w[6][1]},{w[7]}\n")
    file.close()
    
    #create faculty schedules----------------update this
    for v in faculty_list_1:
        file_name = f"{v.faculty}.csv"
        file = open(file_name, "w")
        file.write("Course Name,Course Section,Modality,Lecture Times,Lecture Days,Lab Times,Lab Days\n")
        if len(v.courses) == 0:
            file.write(f"no assigned courses\n")
        else:
            for w in v.courses:
                if w[3] == "ON":
                    file.write(f"{w[0]},{w[1]},{w[3]},NA,NA,NA,NA\n")
                if w[3] == "HY":
                    file.write(f"{w[0]},{w[1]},{w[3]},NA,NA,{w[6][0]} - {w[6][1]},{w[7]}\n")
                else:
                    file.write(f"{w[0]},{w[1]},{w[3]},{w[4][0]} - {w[4][1]},{w[5]},{w[6][0]} - {w[6][1]},{w[7]}\n")
        file.close()
        
    #print out unmatched courses
    
    file = open(Unassigned_courses, "w")
    
    file.write("Course Name,Section Number,Modality,Lecture Times,Lecture Days,Lab Times,Labs Days\n")
    for i, v in enumerate(course_list_1):
        if assigned_courses_1[i] == 1:
            if v.modality == "ON":
                file.write(f"{v.course_name},{v.sec},{v.modality},NA,NA,NA,NA")
            if v.modality == "HY":
                file.write(f"{v.course_name},{v.sec},{v.modality},NA,NA,{v.lab_times[0]} - {v.lab_times[1]},{v.lab_days}")
            else:
                file.write(f"{v.course_name},{v.sec},{v.modality},{v.lecture_times[0]} - {v.lecture_times[1]},{v.lecture_days},{v.lab_times[0]} - {v.lab_times[1]},{v.lab_days}")
            file.write("\n")
            
    file.close()
                
    #creatae PDF version of the error log
    # error_log.close()
    # PDF_file = open(log_name, "r")
    # pdf = FPDF()
    # pdf.add_page()
    # pdf.set_font("Arial", size = 12)
    # for x in PDF_file:
    #     pdf.cell(200, 10, txt = x, ln = 1, align = 'L')
    # pdf.output(f"{log_name[0:len(log_name) - 4]}.pdf")
    # PDF_file.close()
    
    return


#defined functions----------------------------------------------------------------------------------------------------------------------
    #builds up faculty, course, and manager classes--------------------------------------
    
    #generates a faculty matrix
def generate_faculty_schedule(weight: float, d_pref: list, t_pref: list) -> list:
    schedule: list = []
    max: float = 100
    for i in range(0, 4):
        schedule.append([])
        for j in range(9, 17):
            schedule[i].append(probability(weight, d_pref, t_pref, i, j))
            if max < schedule[i][j - 9]:
                max = schedule[i][j - 9]
    for i in range(0, 4):
        for j in range(0, 8):
            schedule[i][j] = schedule[i][j] / max
    return schedule 
    
    #generate course matrix
def generate_course_schedule(LaTimes: list, Labs: list, LeTimes: list, Lecture: list, modality: str) -> list:
    base: list = [[0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    if modality == "ON":
        return [[0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022], [0.022, 0.022, 0.022, 0.022, 0.022]]
    if modality == "HY":
        Lecture: list = [0, 0, 0, 0, 0]
        LeTimes: list = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    else:
        LeTimes = Times_to_list(LeTimes)
    LaTimes = Times_to_list(LaTimes)
    
    #build base matrix
    N = 0
    for i in range(0, 4):
        for j in range(0, 8):
            base[j][i] = second_binary_output(LaTimes[j] * Labs[i] + LeTimes[j] * Lecture[i])
            if base[j][i] > 0:
                N += 1
    
    #normalize the matrix
    if N == 0:
        return base
    
    for i in range(0, 4):
        for j in range(0, 8):
            base[j][i] = base[j][i] / N
    
    return base 

    #return a schedule with faculty
def schedule_builder(faculty_list: list, course_list: list) -> tuple:
    
    #test that overlap scores are printed
    faculty_alignment_matrix = []
    manager_alignment_matrix = []
    combined_score_matrix = []
    course_names = []
    assigned_courses = []
    
    shuffle(course_list)
    for i, v in enumerate(course_list):
        course_names.append([f"{v.course_name} {v.sec}"])
        faculty_alignment_matrix.append([])
        manager_alignment_matrix.append([])
        combined_score_matrix.append([])
        for w in faculty_list:
            alignment = w.overlap(v)
            faculty_alignment_matrix[i].append(alignment[0])
            manager_alignment_matrix[i].append(alignment[1])
            combined_score_matrix[i].append(alignment[0] * (1 - manager_weight) + alignment[1] * manager_weight)
    
    #creates a course overlap score
    course_overlaps = []
    for i, v in enumerate(course_list):
        course_overlaps.append([])
        for w in course_list:
            course_overlaps[i].append(v.overlap(w))
    
    #assign courses
    score = 0
    for i, v in enumerate(course_list):
        faculty_list, combined_score_matrix, course_overlaps, match, score = faculty_course_match(v, i, course_overlaps, combined_score_matrix, faculty_list, score)
        assigned_courses.append(match)
            
    return faculty_list, course_list, assigned_courses, score

    #find the best match for a given course
def faculty_course_match(course, index: int, course_overlap: list, course_list: list, faculty_list: list, score: float) -> tuple:
    m = max(course_list[index])
    if m == 0:
        return faculty_list, course_list, course_overlap, 0, score
    score += m
    faculty = course_list[index].index(m)
    faculty_list[faculty].add_course(course)
        
    #clear out overlaps with course
    for i, v in enumerate(course_list[index]):
        course_list[index][i] = 0
        
    #clear out overlapping courses with a faculty member assigned to the course
    if faculty_list[faculty].hours >= max_hours:
        for v in course_list:
            v[faculty] = 0
    else:  
        for i, v in enumerate(course_list):
            if course_overlap[i][faculty] > 0:
                v[faculty] = 0
    
    return faculty_list, course_list, course_overlap, 1, score
    
    #helper functions----------------------------------------------
    
     
    #punch out the faculty member
def punch_faculty() -> list:
    updated_matrix: list = []
    for i in range(0, 5):
        updated_matrix.append([])
        for j in range(0,9):
            updated_matrix[i].append(0)
    return updated_matrix
    
    #punch out the course and update matrix
def punch_course(faculty: list, course: list) -> list:
    updated_matrix: list = []
    for i in range(0, 5):
        updated_matrix.append([])
        for j in range(0,9):
            updated_matrix[i].append(faculty[i][j] * (1 - course[i][j]))
    return updated_matrix
    
    #extracts user ID from email
def get_id(email: str) -> str:
    end = email.find("@")
    user_id = email[0:end - 1]
    return user_id
    
    #converts course times to a list
def Course_time_to_array(Lower: str, Upper: str) -> list:
    Lower = Lower[0:2].replace(":", "")
    Upper = Upper[0:2].replace(":", "")
    return [int(Lower), int(Upper)]
            
    #probability function
def probability(weight: float, d_pref: list, t_pref: list, i: int, j: int) -> float:
    a = (0.01 + weight) * math.exp(-(i - d_pref[i])^2) #day weight
    b = (1.01 - weight) * (0.01 + t_pref[0]) * math.exp(-(9 - j)^2)
    c = (1.01 - weight) * (0.01 + t_pref[1]) * math.exp(-(12 - j)^2)
    d = (1.01 - weight) * (0.01 + t_pref[2]) * math.exp(-(15 - j)^2)
    return a + b + c + d
    
    #convert days of week to list
def Days_of_week_to_list(value: str) -> list:
    list = [0, 0, 0, 0, 0]
    if value.find("M") > -1:
        list[0] = 1
    if value.find("W") > -1:
        list[2] = 1
    if value.find("F") > -1:
        list[4] = 1
    if value.find("T") > -1:
        if value.find("Th") > -1: 
            list[3] = 1
        if value.find("Th") == -1:
            list[1] = 1
        if value.find("TT") > -1:
            list[3] = 1
            list[1] = 1
            
    return list

    #convert to times of day
def Times_of_day_to_list(value: str) -> list:
    list = [binary_output(value.find("Morning")), binary_output(value.find("Midday")), binary_output(value.find("Afternoon"))]
    return list
    
    #return 1 or 0 for values
def binary_output(number: int) -> int:
    if number > -1:
        return 1
    return 0

    #return 1 or 0 for values
def second_binary_output(number: int) -> int:
    if number > 0:
        return 1
    return 0

#convert times to a list
def Times_to_list(times : list) -> list:
    listtimes = []
    for i in range(0, 9):
        if int(times[0]) <= i + 8 and int(times[1]) >= i + 8:
            listtimes.append(1)
        else:
            listtimes.append(0)
    return listtimes

    #convert campus to matrix
def preferences_to_list(faculty_pref: str, manager_pref: str, dictionary: dict) -> list:
    #establish manager preferences
    if len(manager_pref) != 0:
        manager_list: list = [0]* len(dictionary)
        for i, v in enumerate(manager_pref.split(",")):
            manager_list[dictionary[v]] = 1
    else:
        manager_list: list = [1] * len(dictionary)
    
    #establish faculty preferences
    if len(faculty_pref) != 0:
        faculty_list: list = [0]* len(dictionary)
        for i, v in enumerate(faculty_pref.split(",")):
            faculty_list[dictionary[v]] = 1
    else:
        faculty_list: list = [1]* len(dictionary)
                
    return [faculty_list, manager_list]

#classes-------------------------------------------------------------------------------------------------------------------------------------
    #faculty class
class faculty:
    def __init__(self, name: str, id: str, weight: float, d_pref: str, t_pref: str, c_preff: str, camp_preff: str,  c_prefm: str, camp_prefm: str, m_pref: str, m_prefm: str) -> None:
        self.faculty = name 
        self.faculty_id = id
        self.dp = d_pref
        self.tp = t_pref
        self.cp = c_preff
        self.campus = camp_preff
        self.campus_preferences = preferences_to_list(camp_preff, camp_prefm, Campus_dictionary)
        self.course_preferences = preferences_to_list(c_preff, c_prefm, Course_dictionary)
        self.modality_preferences = preferences_to_list(m_pref, m_prefm, Modality_dictionary)
        self.hours = 0
        self.courses = []
        self.matrix = generate_faculty_schedule(weight, Days_of_week_to_list(d_pref), Times_of_day_to_list(t_pref))
        
    def __str__(self) -> str:
        return f"the schedule preference for {self.faculty}"
    
    def __repr__(self) -> str:
       return "this class is used to keep faculty preferences along with their names and IDs"
    
    def overlap(self, course) -> list:
        overlap_f = 0
        for i in range(0, 4):
            for j in range(0, 8):
                overlap_f += self.matrix[i][j] * course.matrix[j][i] 
        overlap_f = overlap_f * self.campus_preferences[0][Campus_dictionary[course.campus]] * self.course_preferences[0][Course_dictionary[course.course_name]]
        overlap_m = overlap_f * self.campus_preferences[1][Campus_dictionary[course.campus]] * self.course_preferences[1][Course_dictionary[course.course_name]]
        return [overlap_f, overlap_m]
    
    def add_course(self, course) -> None:
        self.courses.append([course.course_name, course.sec, course.matrix, course.modality, course.lecture_times, course.lecture_days, course.lab_times, course.lab_days])
        self.hours += course.hours
        if self.hours >= max_hours:
            self.matrix = [[0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0]]
        return
        
                
    #course class-----------------------
class CourseMaker:
    def __init__(self, course: str, section: int, Lectime: list, LecDOW: list, Labtime: list, LaDOW: list, hours: int, campus: str, modality: str, lecture_times: list, lecture_DOW: str, lab_times: list, lab_DOW: str) -> None:
        self.course_name = course
        self.campus = campus
        self.sec = section
        self.hours = hours
        self.modality = modality
        self.lecture_times = lecture_times
        self.lecture_days = lecture_DOW
        self.lab_times = lab_times
        self.lab_days = lab_DOW
        self.matrix = generate_course_schedule(Labtime, LaDOW, Lectime, LecDOW, modality)

    def __str__(self) -> str:
        return f"the schedule for {self.matrix}"
    
    def __repr__(self) -> str:
       return "this class is used to create courses"

    def overlap(self, course) -> list:
        overlap = 0
        for i in range(0, 4):
            for j in range(0, 8):
                overlap += self.matrix[j][i] * course.matrix[j][i] 
        return overlap
       
#execute main
if __name__ == "__main__":
  main()
  