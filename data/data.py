class Data:

    def __init__(self, entreprise, montant):
        self.entreprise = entreprise
        self.montant = montant

    def __str__(self):
        return f"Entreprise : {self.entreprise}, Montant : {self.montant} CHF"