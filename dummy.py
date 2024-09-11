import server as sv
import utils as u

# test

print("running")

sv.list_files()

id = sv.get_id_by_name("domains.json")

data = sv.read_json_file(id)

u.print_dict({"" : data})