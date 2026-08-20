class Particle:
    def __init__(self, particle_id, particle_type, properties):
        self.id = particle_id
        self.type = particle_type  # e.g., 'electron', 'positron', 'photon'
        self.properties = properties  # could store mass, charge, energy, etc.
        self.parents = []
        self.children = []

    def add_parent(self, parent_particle):
        self.parents.append(parent_particle)

    def add_child(self, child_particle):
        self.children.append(child_particle)

# Example usage:
electron1 = Particle("electron1", "electron", {"charge": -1})
positron1 = Particle("positron1", "positron", {"charge": +1})
photon1 = Particle("photon1", "photon", {"energy": None})

# You can then model photon formation:
photon1.parents = [electron1, positron1]
