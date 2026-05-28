// Exemple de code WLangage - logique metier
// Calcul d'une facture avec remise

gTauxTVA is real = 20.0

PROCEDURE CalculerTotalHT(nPrixUnitaire is real, nQuantite is int)
	nTotal is real
	nTotal = nPrixUnitaire * nQuantite
	// remise de 10% au dela de 100 euros
	IF nTotal > 100 THEN
		nTotal = nTotal * 0.9
	ELSE
		nTotal = nTotal
	END
	RETURN nTotal
END

PROCEDURE CalculerTTC(nMontantHT is real)
	nTVA is real = nMontantHT * gTauxTVA / 100
	RETURN nMontantHT + nTVA
END

PROCEDURE FormaterClient(sNom is string, sPrenom is string)
	sResultat is string
	sResultat = Majuscule(sNom) + " " + sPrenom
	IF Taille(sResultat) = 0 THEN
		sResultat = "INCONNU"
	END
	RETURN sResultat
END

PROCEDURE Mention(nNote is int)
	sMention is string
	SWITCH nNote
		CASE 0, 1, 2: sMention = "Insuffisant"
		CASE 3: sMention = "Passable"
		OTHER: sMention = "Bien"
	END
	RETURN sMention
END

PROCEDURE Cumul(nMax is int)
	nSomme is int = 0
	FOR i = 1 TO nMax
		nSomme = nSomme + i
	END
	RETURN nSomme
END

// Programme principal de demonstration
nFacture is real
nFacture = CalculerTotalHT(50.0, 3)
Trace("Total HT : ", nFacture)
Trace("Total TTC : ", CalculerTTC(nFacture))
Trace(FormaterClient("dupont", "Jean"))
