from database import engine, SessionLocal, Base
from models import User, Assessment, Question, TestCase, DefectHistory
import json
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # ============ USERS ============
    users = [
        User(username="student1", password_hash=hash_password("student123"), full_name="Priya Sharma", role="student"),
        User(username="student2", password_hash=hash_password("student123"), full_name="Rahul Mehta", role="student"),
        User(username="tester1", password_hash=hash_password("tester123"), full_name="Ananya Reddy", role="tester"),
        User(username="tester2", password_hash=hash_password("tester123"), full_name="Vikram Patel", role="tester"),
        User(username="testlead", password_hash=hash_password("lead123"), full_name="Dr. Suresh Kumar", role="test_lead"),
        User(username="admin", password_hash=hash_password("admin123"), full_name="System Admin", role="admin"),
    ]
    db.add_all(users)

    # ============ ASSESSMENTS ============
    assessments = [
        Assessment(title="Data Structures & Algorithms", description="Covers arrays, linked lists, trees, graphs, sorting and searching algorithms.", duration_minutes=45, total_questions=15, passing_score=60),
        Assessment(title="Database Management Systems", description="Relational algebra, SQL queries, normalization, transactions and concurrency.", duration_minutes=30, total_questions=10, passing_score=50),
        Assessment(title="Computer Networks", description="OSI model, TCP/IP, routing protocols, network security fundamentals.", duration_minutes=40, total_questions=12, passing_score=55),
    ]
    db.add_all(assessments)
    db.flush()

    # ============ QUESTIONS ============
    dsa_questions = [
        Question(assessment_id=1, question_text="What is the time complexity of binary search?", option_a="O(n)", option_b="O(log n)", option_c="O(n²)", option_d="O(1)", correct_option="B", marks=2),
        Question(assessment_id=1, question_text="Which data structure uses LIFO principle?", option_a="Queue", option_b="Stack", option_c="Array", option_d="Linked List", correct_option="B", marks=2),
        Question(assessment_id=1, question_text="What is the worst-case time complexity of Quick Sort?", option_a="O(n log n)", option_b="O(n)", option_c="O(n²)", option_d="O(log n)", correct_option="C", marks=2),
        Question(assessment_id=1, question_text="Which traversal visits root node first?", option_a="Inorder", option_b="Preorder", option_c="Postorder", option_d="Level order", correct_option="B", marks=2),
        Question(assessment_id=1, question_text="What is a balanced binary search tree?", option_a="AVL Tree", option_b="Linked List", option_c="Stack", option_d="Queue", correct_option="A", marks=2),
        Question(assessment_id=1, question_text="Which algorithm uses divide and conquer?", option_a="Bubble Sort", option_b="Merge Sort", option_c="Linear Search", option_d="Insertion Sort", correct_option="B", marks=2),
        Question(assessment_id=1, question_text="What is the space complexity of BFS?", option_a="O(1)", option_b="O(V)", option_c="O(E)", option_d="O(V+E)", correct_option="B", marks=2),
        Question(assessment_id=1, question_text="Hash table lookup average time complexity?", option_a="O(n)", option_b="O(1)", option_c="O(log n)", option_d="O(n²)", correct_option="B", marks=2),
        Question(assessment_id=1, question_text="Which is not a stable sorting algorithm?", option_a="Merge Sort", option_b="Bubble Sort", option_c="Quick Sort", option_d="Insertion Sort", correct_option="C", marks=2),
        Question(assessment_id=1, question_text="Dijkstra's algorithm finds?", option_a="Minimum spanning tree", option_b="Shortest path", option_c="Maximum flow", option_d="Topological order", correct_option="B", marks=2),
        Question(assessment_id=1, question_text="Which data structure is used in BFS?", option_a="Stack", option_b="Queue", option_c="Heap", option_d="Array", correct_option="B", marks=1),
        Question(assessment_id=1, question_text="What is a complete binary tree?", option_a="All leaves at same level", option_b="All levels filled except possibly last", option_c="Every node has 2 children", option_d="Height balanced tree", correct_option="B", marks=1),
        Question(assessment_id=1, question_text="Red-Black tree is a type of?", option_a="B-tree", option_b="Self-balancing BST", option_c="Heap", option_d="Trie", correct_option="B", marks=1),
        Question(assessment_id=1, question_text="Which is used for priority queue implementation?", option_a="Stack", option_b="Queue", option_c="Heap", option_d="Array", correct_option="C", marks=1),
        Question(assessment_id=1, question_text="Amortized time complexity of dynamic array insertion?", option_a="O(n)", option_b="O(1)", option_c="O(log n)", option_d="O(n²)", correct_option="B", marks=1),
    ]

    dbms_questions = [
        Question(assessment_id=2, question_text="What does ACID stand for in transactions?", option_a="Atomicity Consistency Isolation Durability", option_b="Addition Calculation Integration Data", option_c="Automated Consistent Isolated Database", option_d="Atomic Calculated Index Durable", correct_option="A", marks=2),
        Question(assessment_id=2, question_text="Which normal form eliminates transitive dependency?", option_a="1NF", option_b="2NF", option_c="3NF", option_d="BCNF", correct_option="C", marks=2),
        Question(assessment_id=2, question_text="What is a primary key?", option_a="Any column", option_b="Unique identifier for each row", option_c="Foreign reference", option_d="Index column", correct_option="B", marks=2),
        Question(assessment_id=2, question_text="SQL command to retrieve data?", option_a="INSERT", option_b="UPDATE", option_c="SELECT", option_d="DELETE", correct_option="C", marks=2),
        Question(assessment_id=2, question_text="Which join returns all rows from both tables?", option_a="INNER JOIN", option_b="LEFT JOIN", option_c="RIGHT JOIN", option_d="FULL OUTER JOIN", correct_option="D", marks=2),
        Question(assessment_id=2, question_text="What is a deadlock?", option_a="Fast query", option_b="Circular wait condition", option_c="Index rebuild", option_d="Table lock", correct_option="B", marks=2),
        Question(assessment_id=2, question_text="Which is a DDL command?", option_a="SELECT", option_b="INSERT", option_c="CREATE TABLE", option_d="UPDATE", correct_option="C", marks=1),
        Question(assessment_id=2, question_text="What does a foreign key reference?", option_a="Same table", option_b="Primary key of another table", option_c="Index", option_d="View", correct_option="B", marks=1),
        Question(assessment_id=2, question_text="What is normalization?", option_a="Adding redundancy", option_b="Reducing redundancy", option_c="Creating indexes", option_d="Deleting tables", correct_option="B", marks=1),
        Question(assessment_id=2, question_text="What is an index used for?", option_a="Data encryption", option_b="Faster data retrieval", option_c="Data backup", option_d="Data deletion", correct_option="B", marks=1),
    ]

    cn_questions = [
        Question(assessment_id=3, question_text="How many layers does the OSI model have?", option_a="5", option_b="6", option_c="7", option_d="4", correct_option="C", marks=2),
        Question(assessment_id=3, question_text="Which protocol operates at the transport layer?", option_a="HTTP", option_b="TCP", option_c="IP", option_d="Ethernet", correct_option="B", marks=2),
        Question(assessment_id=3, question_text="What does DNS stand for?", option_a="Domain Name System", option_b="Data Network Service", option_c="Digital Name Server", option_d="Domain Network System", correct_option="A", marks=2),
        Question(assessment_id=3, question_text="Which device operates at the network layer?", option_a="Hub", option_b="Switch", option_c="Router", option_d="Repeater", correct_option="C", marks=2),
        Question(assessment_id=3, question_text="What is the default port for HTTP?", option_a="21", option_b="22", option_c="80", option_d="443", correct_option="C", marks=2),
        Question(assessment_id=3, question_text="IP address version 4 uses how many bits?", option_a="16", option_b="32", option_c="64", option_d="128", correct_option="B", marks=1),
        Question(assessment_id=3, question_text="What is DHCP used for?", option_a="Routing", option_b="Dynamic IP assignment", option_c="File transfer", option_d="Email", correct_option="B", marks=1),
        Question(assessment_id=3, question_text="Which protocol is connectionless?", option_a="TCP", option_b="UDP", option_c="FTP", option_d="HTTP", correct_option="B", marks=1),
        Question(assessment_id=3, question_text="What is a subnet mask?", option_a="IP filter", option_b="Network/host identifier", option_c="MAC address", option_d="Port number", correct_option="B", marks=1),
        Question(assessment_id=3, question_text="What does ARP resolve?", option_a="IP to domain", option_b="IP to MAC address", option_c="MAC to IP", option_d="Domain to IP", correct_option="B", marks=1),
        Question(assessment_id=3, question_text="What layer does SSL/TLS operate at?", option_a="Network", option_b="Transport", option_c="Session/Presentation", option_d="Application", correct_option="C", marks=1),
        Question(assessment_id=3, question_text="Maximum payload of an Ethernet frame?", option_a="1000 bytes", option_b="1500 bytes", option_c="2000 bytes", option_d="4096 bytes", correct_option="B", marks=1),
    ]

    db.add_all(dsa_questions + dbms_questions + cn_questions)

    # ============ TEST CASES (30+ realistic test cases) ============
    test_cases = [
        TestCase(test_case_id="TC001", name="Student Login Authentication", module="Authentication",
                 critical_user_journey="Login", description="Verify student can login with valid credentials and is redirected to dashboard",
                 business_criticality=8.5, historical_defect_count=12, historical_critical_defect_count=3,
                 production_usage=9.8, change_risk=5.0, network_risk=6.0, unusual_behaviour_risk=3.0,
                 execution_time_minutes=2.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC002", name="Invalid Login Rejection", module="Authentication",
                 critical_user_journey="Login", description="Verify system rejects invalid credentials with appropriate error message",
                 business_criticality=8.0, historical_defect_count=8, historical_critical_defect_count=2,
                 production_usage=9.5, change_risk=4.5, network_risk=5.0, unusual_behaviour_risk=4.0,
                 execution_time_minutes=1.5, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC003", name="Assessment Selection", module="Assessment",
                 critical_user_journey="Assessment Selection", description="Verify student can view and select available assessments from the list",
                 business_criticality=7.5, historical_defect_count=6, historical_critical_defect_count=1,
                 production_usage=9.0, change_risk=4.0, network_risk=3.0, unusual_behaviour_risk=2.0,
                 execution_time_minutes=2.5, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC004", name="Assessment Instructions Display", module="Assessment",
                 critical_user_journey="Assessment Preparation", description="Verify complete instructions are displayed before starting assessment",
                 business_criticality=5.5, historical_defect_count=3, historical_critical_defect_count=0,
                 production_usage=8.5, change_risk=2.5, network_risk=2.0, unusual_behaviour_risk=1.0,
                 execution_time_minutes=1.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC005", name="Start Assessment Workflow", module="Assessment",
                 critical_user_journey="Start Assessment", description="Verify assessment starts correctly with timer initialization and question loading",
                 business_criticality=9.0, historical_defect_count=15, historical_critical_defect_count=5,
                 production_usage=9.5, change_risk=7.0, network_risk=5.0, unusual_behaviour_risk=4.0,
                 execution_time_minutes=3.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC006", name="Question Loading and Display", module="Assessment",
                 critical_user_journey="Question Display", description="Verify all questions load correctly with options and navigation",
                 business_criticality=8.5, historical_defect_count=10, historical_critical_defect_count=3,
                 production_usage=9.5, change_risk=6.0, network_risk=4.0, unusual_behaviour_risk=3.0,
                 execution_time_minutes=2.5, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC007", name="Timer Countdown Functionality", module="Timer",
                 critical_user_journey="Timer", description="Verify timer counts down correctly and auto-submits when time expires",
                 business_criticality=9.5, historical_defect_count=18, historical_critical_defect_count=6,
                 production_usage=9.8, change_risk=8.0, network_risk=3.0, unusual_behaviour_risk=5.0,
                 execution_time_minutes=4.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC008", name="Answer Selection and Storage", module="Assessment",
                 critical_user_journey="Answer Submission", description="Verify selected answers are stored correctly in the system",
                 business_criticality=9.0, historical_defect_count=14, historical_critical_defect_count=4,
                 production_usage=9.8, change_risk=6.5, network_risk=4.0, unusual_behaviour_risk=3.5,
                 execution_time_minutes=3.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC009", name="Answer Autosave Mechanism", module="Autosave",
                 critical_user_journey="Autosave", description="Verify answers are automatically saved at regular intervals without user action",
                 business_criticality=9.2, historical_defect_count=20, historical_critical_defect_count=7,
                 production_usage=9.5, change_risk=8.5, network_risk=7.0, unusual_behaviour_risk=6.0,
                 execution_time_minutes=4.5, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC010", name="Network Disconnection Detection", module="Network",
                 critical_user_journey="Network Recovery", description="Verify system detects network disconnection and shows appropriate warning",
                 business_criticality=8.8, historical_defect_count=22, historical_critical_defect_count=8,
                 production_usage=7.5, change_risk=7.5, network_risk=9.5, unusual_behaviour_risk=7.0,
                 execution_time_minutes=5.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC011", name="Network Reconnection Recovery", module="Network",
                 critical_user_journey="Network Recovery", description="Verify system recovers gracefully after network reconnection and syncs data",
                 business_criticality=9.0, historical_defect_count=25, historical_critical_defect_count=9,
                 production_usage=7.5, change_risk=8.0, network_risk=9.8, unusual_behaviour_risk=8.0,
                 execution_time_minutes=5.5, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC012", name="Assessment Submission", module="Submission",
                 critical_user_journey="Submit Assessment", description="Verify final assessment submission processes correctly with all answers",
                 business_criticality=9.8, historical_defect_count=16, historical_critical_defect_count=6,
                 production_usage=9.8, change_risk=7.0, network_risk=6.0, unusual_behaviour_risk=5.0,
                 execution_time_minutes=3.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC013", name="Submission Confirmation Page", module="Submission",
                 critical_user_journey="Submission Confirmation", description="Verify confirmation page displays after successful submission with details",
                 business_criticality=6.5, historical_defect_count=4, historical_critical_defect_count=1,
                 production_usage=9.0, change_risk=3.0, network_risk=2.0, unusual_behaviour_risk=1.5,
                 execution_time_minutes=1.5, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC014", name="Result Generation and Display", module="Results",
                 critical_user_journey="Result Generation", description="Verify results are calculated correctly and displayed to the student",
                 business_criticality=8.0, historical_defect_count=11, historical_critical_defect_count=3,
                 production_usage=9.0, change_risk=5.5, network_risk=3.0, unusual_behaviour_risk=2.5,
                 execution_time_minutes=3.5, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC015", name="Session Timeout Handling", module="Session",
                 critical_user_journey="Session Management", description="Verify system handles session timeout gracefully during assessment",
                 business_criticality=7.5, historical_defect_count=9, historical_critical_defect_count=3,
                 production_usage=6.0, change_risk=5.0, network_risk=4.0, unusual_behaviour_risk=5.0,
                 execution_time_minutes=4.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC016", name="Unauthorized Assessment Access", module="Security",
                 critical_user_journey="Access Control", description="Verify unauthorized users cannot access assessments they are not enrolled in",
                 business_criticality=8.5, historical_defect_count=7, historical_critical_defect_count=4,
                 production_usage=5.0, change_risk=4.0, network_risk=2.0, unusual_behaviour_risk=6.0,
                 execution_time_minutes=2.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC017", name="Browser Refresh During Assessment", module="Resilience",
                 critical_user_journey="State Recovery", description="Verify assessment state is preserved when browser is refreshed mid-exam",
                 business_criticality=8.0, historical_defect_count=13, historical_critical_defect_count=4,
                 production_usage=7.0, change_risk=6.5, network_risk=3.0, unusual_behaviour_risk=5.5,
                 execution_time_minutes=3.5, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC018", name="Duplicate Answer Event Handling", module="Event Processing",
                 critical_user_journey="Event Resilience", description="Verify duplicate answer submissions do not corrupt assessment state",
                 business_criticality=8.5, historical_defect_count=11, historical_critical_defect_count=5,
                 production_usage=6.5, change_risk=7.0, network_risk=5.0, unusual_behaviour_risk=8.5,
                 execution_time_minutes=3.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC019", name="Out-of-Order Event Processing", module="Event Processing",
                 critical_user_journey="Event Resilience", description="Verify system handles events received out of chronological order",
                 business_criticality=8.0, historical_defect_count=9, historical_critical_defect_count=4,
                 production_usage=5.0, change_risk=7.5, network_risk=6.0, unusual_behaviour_risk=9.0,
                 execution_time_minutes=4.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC020", name="Delayed Save After Submission", module="Event Processing",
                 critical_user_journey="Event Resilience", description="Verify late-arriving save events after submission do not alter final state",
                 business_criticality=8.5, historical_defect_count=8, historical_critical_defect_count=3,
                 production_usage=5.5, change_risk=6.5, network_risk=7.0, unusual_behaviour_risk=8.0,
                 execution_time_minutes=3.5, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC021", name="Multiple Assessment Enrollment", module="Assessment",
                 critical_user_journey="Assessment Selection", description="Verify student can view and manage multiple assessment enrollments",
                 business_criticality=5.0, historical_defect_count=4, historical_critical_defect_count=0,
                 production_usage=7.0, change_risk=3.0, network_risk=2.0, unusual_behaviour_risk=1.5,
                 execution_time_minutes=2.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC022", name="Question Navigation (Next/Previous)", module="Assessment",
                 critical_user_journey="Question Navigation", description="Verify forward and backward navigation between questions works correctly",
                 business_criticality=7.0, historical_defect_count=7, historical_critical_defect_count=2,
                 production_usage=9.0, change_risk=4.0, network_risk=2.0, unusual_behaviour_risk=2.5,
                 execution_time_minutes=2.5, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC023", name="Answer Modification Before Submit", module="Assessment",
                 critical_user_journey="Answer Management", description="Verify students can change their answers before final submission",
                 business_criticality=7.5, historical_defect_count=6, historical_critical_defect_count=1,
                 production_usage=8.5, change_risk=4.5, network_risk=2.0, unusual_behaviour_risk=3.0,
                 execution_time_minutes=2.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC024", name="Timer Warning at 5 Minutes", module="Timer",
                 critical_user_journey="Timer", description="Verify visual and audio warning when timer reaches 5 minutes remaining",
                 business_criticality=6.0, historical_defect_count=5, historical_critical_defect_count=1,
                 production_usage=8.0, change_risk=3.5, network_risk=1.0, unusual_behaviour_risk=2.0,
                 execution_time_minutes=2.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC025", name="Concurrent Session Prevention", module="Security",
                 critical_user_journey="Session Security", description="Verify student cannot have multiple active assessment sessions simultaneously",
                 business_criticality=8.0, historical_defect_count=6, historical_critical_defect_count=3,
                 production_usage=4.5, change_risk=5.5, network_risk=3.0, unusual_behaviour_risk=6.5,
                 execution_time_minutes=3.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC026", name="Score Calculation Accuracy", module="Results",
                 critical_user_journey="Result Generation", description="Verify score is calculated correctly based on correct answers and marks distribution",
                 business_criticality=9.0, historical_defect_count=8, historical_critical_defect_count=4,
                 production_usage=9.0, change_risk=5.0, network_risk=1.0, unusual_behaviour_risk=2.0,
                 execution_time_minutes=3.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC027", name="Assessment Time Limit Enforcement", module="Timer",
                 critical_user_journey="Timer", description="Verify assessment auto-submits exactly when time limit is reached",
                 business_criticality=9.0, historical_defect_count=12, historical_critical_defect_count=5,
                 production_usage=9.5, change_risk=7.0, network_risk=2.0, unusual_behaviour_risk=4.0,
                 execution_time_minutes=4.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC028", name="Student Dashboard Data Loading", module="Dashboard",
                 critical_user_journey="Dashboard", description="Verify dashboard loads with correct enrollment, scores, and upcoming assessments",
                 business_criticality=5.0, historical_defect_count=5, historical_critical_defect_count=0,
                 production_usage=8.0, change_risk=3.5, network_risk=3.0, unusual_behaviour_risk=1.0,
                 execution_time_minutes=2.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC029", name="Logout and Session Cleanup", module="Authentication",
                 critical_user_journey="Session Management", description="Verify logout clears session and prevents back-button access to assessment",
                 business_criticality=6.5, historical_defect_count=4, historical_critical_defect_count=1,
                 production_usage=7.0, change_risk=3.0, network_risk=2.0, unusual_behaviour_risk=3.0,
                 execution_time_minutes=2.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC030", name="Partial Submission Recovery", module="Submission",
                 critical_user_journey="Submit Assessment", description="Verify system can recover and process partial submissions after failures",
                 business_criticality=8.5, historical_defect_count=10, historical_critical_defect_count=4,
                 production_usage=4.0, change_risk=7.5, network_risk=8.0, unusual_behaviour_risk=7.0,
                 execution_time_minutes=5.0, is_mandatory=True, current_status="Active"),

        TestCase(test_case_id="TC031", name="Assessment Access Window Validation", module="Assessment",
                 critical_user_journey="Access Control", description="Verify assessments can only be started within their permitted time window",
                 business_criticality=6.0, historical_defect_count=3, historical_critical_defect_count=1,
                 production_usage=6.5, change_risk=3.0, network_risk=1.0, unusual_behaviour_risk=2.0,
                 execution_time_minutes=2.5, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC032", name="Network Latency Impact on Autosave", module="Network",
                 critical_user_journey="Autosave", description="Verify autosave functions correctly under high network latency conditions",
                 business_criticality=7.5, historical_defect_count=7, historical_critical_defect_count=2,
                 production_usage=6.0, change_risk=5.5, network_risk=9.0, unusual_behaviour_risk=5.0,
                 execution_time_minutes=4.5, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC033", name="Input Validation on Answer Fields", module="Validation",
                 critical_user_journey="Answer Submission", description="Verify system validates answer inputs and rejects malformed data",
                 business_criticality=6.5, historical_defect_count=5, historical_critical_defect_count=1,
                 production_usage=7.5, change_risk=3.5, network_risk=1.0, unusual_behaviour_risk=4.0,
                 execution_time_minutes=2.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC034", name="Assessment Load Under Concurrent Users", module="Performance",
                 critical_user_journey="System Performance", description="Verify system handles multiple students taking assessments simultaneously",
                 business_criticality=7.0, historical_defect_count=6, historical_critical_defect_count=2,
                 production_usage=8.0, change_risk=5.0, network_risk=6.0, unusual_behaviour_risk=4.0,
                 execution_time_minutes=6.0, is_mandatory=False, current_status="Active"),

        TestCase(test_case_id="TC035", name="Role-Based Dashboard Rendering", module="Authorization",
                 critical_user_journey="Access Control", description="Verify different roles see appropriate dashboard content and navigation options",
                 business_criticality=7.0, historical_defect_count=4, historical_critical_defect_count=1,
                 production_usage=8.0, change_risk=4.5, network_risk=1.0, unusual_behaviour_risk=2.0,
                 execution_time_minutes=2.5, is_mandatory=False, current_status="Active"),
    ]
    db.add_all(test_cases)

    # ============ DEFECT HISTORY ============
    defects = [
        DefectHistory(test_case_id="TC007", defect_id="DEF001", severity="Critical", module="Timer", description="Timer freezes when browser tab is minimized during assessment", detected_date="2024-03-15", resolved=True, resolution_time_hours=8.0),
        DefectHistory(test_case_id="TC007", defect_id="DEF002", severity="Critical", module="Timer", description="Timer shows negative values after reaching zero before auto-submit triggers", detected_date="2024-06-20", resolved=True, resolution_time_hours=4.0),
        DefectHistory(test_case_id="TC007", defect_id="DEF003", severity="High", module="Timer", description="Timer drift of 2-3 seconds per 30-minute session due to JavaScript imprecision", detected_date="2024-08-10", resolved=True, resolution_time_hours=12.0),
        DefectHistory(test_case_id="TC009", defect_id="DEF004", severity="Critical", module="Autosave", description="Autosave overwrites newer answers with older cached data on slow connections", detected_date="2024-02-28", resolved=True, resolution_time_hours=16.0),
        DefectHistory(test_case_id="TC009", defect_id="DEF005", severity="Critical", module="Autosave", description="Autosave fails silently when storage quota is exceeded", detected_date="2024-05-12", resolved=True, resolution_time_hours=6.0),
        DefectHistory(test_case_id="TC009", defect_id="DEF006", severity="High", module="Autosave", description="Race condition when autosave and manual save trigger simultaneously", detected_date="2024-07-30", resolved=False, resolution_time_hours=None),
        DefectHistory(test_case_id="TC011", defect_id="DEF007", severity="Critical", module="Network", description="Data loss when reconnecting after extended network outage exceeding 5 minutes", detected_date="2024-01-15", resolved=True, resolution_time_hours=24.0),
        DefectHistory(test_case_id="TC011", defect_id="DEF008", severity="Critical", module="Network", description="Duplicate submissions triggered during network reconnection handshake", detected_date="2024-04-22", resolved=True, resolution_time_hours=10.0),
        DefectHistory(test_case_id="TC011", defect_id="DEF009", severity="High", module="Network", description="Assessment timer continues during disconnection causing premature timeout", detected_date="2024-09-05", resolved=False, resolution_time_hours=None),
        DefectHistory(test_case_id="TC012", defect_id="DEF010", severity="Critical", module="Submission", description="Double-click on submit button creates duplicate submission entries", detected_date="2024-03-01", resolved=True, resolution_time_hours=3.0),
        DefectHistory(test_case_id="TC012", defect_id="DEF011", severity="Critical", module="Submission", description="Submission fails with 500 error when assessment has unanswered mandatory questions", detected_date="2024-06-15", resolved=True, resolution_time_hours=5.0),
        DefectHistory(test_case_id="TC005", defect_id="DEF012", severity="Critical", module="Assessment", description="Assessment starts but questions fail to load when server is under heavy load", detected_date="2024-04-10", resolved=True, resolution_time_hours=8.0),
        DefectHistory(test_case_id="TC005", defect_id="DEF013", severity="High", module="Assessment", description="Wrong assessment loads when student clicks start rapidly between assessments", detected_date="2024-07-25", resolved=True, resolution_time_hours=6.0),
        DefectHistory(test_case_id="TC010", defect_id="DEF014", severity="Critical", module="Network", description="Network disconnection not detected on certain mobile browsers", detected_date="2024-02-10", resolved=True, resolution_time_hours=20.0),
        DefectHistory(test_case_id="TC010", defect_id="DEF015", severity="High", module="Network", description="False positive disconnection alerts on slow but stable connections", detected_date="2024-08-18", resolved=False, resolution_time_hours=None),
        DefectHistory(test_case_id="TC018", defect_id="DEF016", severity="Critical", module="Event Processing", description="Duplicate answer events generate multiple score entries in database", detected_date="2024-05-20", resolved=True, resolution_time_hours=7.0),
        DefectHistory(test_case_id="TC018", defect_id="DEF017", severity="High", module="Event Processing", description="Idempotency check fails when duplicate events arrive within 1ms window", detected_date="2024-09-01", resolved=False, resolution_time_hours=None),
        DefectHistory(test_case_id="TC019", defect_id="DEF018", severity="Critical", module="Event Processing", description="Out-of-order events corrupt student assessment state machine", detected_date="2024-06-08", resolved=True, resolution_time_hours=15.0),
        DefectHistory(test_case_id="TC001", defect_id="DEF019", severity="High", module="Authentication", description="Login session token not invalidated after password change", detected_date="2024-04-05", resolved=True, resolution_time_hours=4.0),
        DefectHistory(test_case_id="TC016", defect_id="DEF020", severity="Critical", module="Security", description="Direct URL manipulation allows access to unauthorized assessment content", detected_date="2024-01-25", resolved=True, resolution_time_hours=2.0),
        DefectHistory(test_case_id="TC017", defect_id="DEF021", severity="Critical", module="Resilience", description="Browser refresh during submission causes partial data loss", detected_date="2024-03-20", resolved=True, resolution_time_hours=10.0),
        DefectHistory(test_case_id="TC030", defect_id="DEF022", severity="Critical", module="Submission", description="Partial submissions marked as complete, preventing student retake", detected_date="2024-07-12", resolved=True, resolution_time_hours=8.0),
        DefectHistory(test_case_id="TC008", defect_id="DEF023", severity="High", module="Assessment", description="Selected answer not visually highlighted after page navigation and return", detected_date="2024-05-30", resolved=True, resolution_time_hours=3.0),
        DefectHistory(test_case_id="TC014", defect_id="DEF024", severity="Critical", module="Results", description="Score calculation wrong when question marks are not uniform", detected_date="2024-08-25", resolved=True, resolution_time_hours=5.0),
        DefectHistory(test_case_id="TC025", defect_id="DEF025", severity="Critical", module="Security", description="Race condition allows two concurrent sessions for same student", detected_date="2024-06-30", resolved=True, resolution_time_hours=12.0),
    ]
    db.add_all(defects)

    db.commit()
    db.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
