import json
from src.showrunner_tool.repositories.event_sourcing_repo import EventService

def test_event_service():
    svc = EventService()
    

    # append
    id1 = svc.append_event(None, 'main', 'CREATE', 'char_1', {'name': 'Alice'})
    id2 = svc.append_event(id1, 'main', 'UPDATE', 'char_1', {'age': 30})
    id3 = svc.append_event(id2, 'main', 'CREATE', 'char_2', {'name': 'Bob'})
    
    state = svc.project_state('main')
    print("Main State:", state)
    assert state['char_1']['name'] == 'Alice'
    assert state['char_1']['age'] == 30
    assert state['char_2']['name'] == 'Bob'
    
    # test branching
    svc.branch('main', 'alt', id1) # branching at point char_1 created
    
    # append on alt branch
    id4 = svc.append_event(id1, 'alt', 'UPDATE', 'char_1', {'name': 'Alice Alter'})
    
    alt_state = svc.project_state('alt')
    print("Alt State:", alt_state)
    assert alt_state['char_1']['name'] == 'Alice Alter'
    assert 'age' not in alt_state['char_1']
    assert 'char_2' not in alt_state
    
    print("Tests passed!")

if __name__ == '__main__':
    test_event_service()
