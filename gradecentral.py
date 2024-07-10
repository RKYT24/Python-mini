import statistics as st
studentGrades={}

def gradecentral():
    print("\t \033[34m Welcome to Grade Central \033[0m \n")
    try:
        while True:
            
            print(f'[1] - Enter grades \t [2] - Remove Student \t [3] - Student average grades \t [4] - Exit')
            choice=int(input("What would you like to do today (write a number) : "))
            
            if choice==1:
                StudName=input("Enter student name: ")
                Marks=int(input("Enter marks: "))
                if StudName in studentGrades:
                    studentGrades[StudName].append(Marks)
                    print('\033[32m Done !\n',studentGrades,'\033[0m')
                else:
                    studentGrades[StudName]=[Marks]
                    print('\033[32m',studentGrades,'\033[0m')
                
            elif choice==2:
                StudName=input("Enter student name: ")
                if StudName in studentGrades:
                    del studentGrades[StudName]
                    print('\033[32m Done !\n',studentGrades,'\033[0m')
                else:
                    print("\033[31m Student not found...!\033[0m")
                    print('\033[32m',studentGrades,'\033[0m')
                
            elif choice==3:    # TODO: Add for one or more students data at a time !
                StudName=input("Enter student name: ")
                if StudName in  studentGrades:
                    print('\033[32m',st.mean(studentGrades[StudName]),'\033[0m')
                else:
                    print("\033[31m Student not found...!\033[0m")
                    print('\033[32m',studentGrades,'\033[0m')
                    
            elif choice==4:
                print("\033[32m Exiting....\033[0m")
                break
            else:
                print("\033[31m Invalid selection ! Please choose from 1 to 4 \033[0m")
                
    except Exception as e:
        print(f"\033[31m An error occrurred : {e}\033[0m")

def login():
    
    for i in range(5):
        username=input("Enter your username : ")
        password=input("Enter password : ")
        if username=='RKYT' and password=='143':
            print("\nUser Authentication successfull !\n --------------------------------------------------------\n \t Welcome Rahul, Glad to see you here 🥰\n --------------------------------------------------------\n")
            gradecentral()
            break
        
        else:
            if i==4:
                print("Sorry , You exceeded the user authentication limit ! \033[31m Closing the program ! \033[0m")
            else:
                print(f'Invalid Username or Password ! \t {4-i} times remaining !')
                
login()