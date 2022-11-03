@startuml
"Not-logged User" as nologged_user
nologged_user -right-> (Register)
nologged_user -right-> (Log in)
nologged_user --> (Monitoring of\nmaterial statistics)
nologged_user--> (Monitoring of\nmaterial price)
nologged_user-left-> (Access to\nunauthorized section)

"Logged user" as logged_user
logged_user --|> nologged_user
logged_user -> (Tracking of their collection)
logged_user -left-> (Changing their details)

Employee --|> logged_user
Employee -> (Confirmation of\ncustomer registration)
Employee -left-> (Tracking of their\ncollection history)

Admin --|> Employee
Admin -> (Managing users)
Admin -left-> (Adjustment of price list)
@enduml
