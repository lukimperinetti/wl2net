// Genere automatiquement par wl2net (WLangage -> C#)
// Verifie les blocs marques TODO : conversion partielle.
using System;
using System.Collections.Generic;
using System.Linq;

namespace MigrationWinDev
{
    public static class facture
    {
        public static double gTauxTVA = 20.0;
        public static double nFacture = 0;

        public static double CalculerTotalHT(double nPrixUnitaire, int nQuantite)
        {
            double nTotal = 0;
            nTotal = (nPrixUnitaire * nQuantite);
            // remise de 10% au dela de 100 euros
            if ((nTotal > 100))
            {
                nTotal = (nTotal * 0.9);
            }
            else
            {
                nTotal = nTotal;
            }
            return nTotal;
        }

        public static double CalculerTTC(double nMontantHT)
        {
            double nTVA = ((nMontantHT * gTauxTVA) / 100);
            return (nMontantHT + nTVA);
        }

        public static string FormaterClient(string sNom, string sPrenom)
        {
            string sResultat = "";
            sResultat = ((sNom.ToUpper() + " ") + sPrenom);
            if ((sResultat.Length == 0))
            {
                sResultat = "INCONNU";
            }
            return sResultat;
        }

        public static string Mention(int nNote)
        {
            string sMention = "";
            switch (nNote)
            {
                case 0:
                case 1:
                case 2:
                    sMention = "Insuffisant";
                    break;
                case 3:
                    sMention = "Passable";
                    break;
                default:
                    sMention = "Bien";
                    break;
            }
            return sMention;
        }

        public static int Cumul(int nMax)
        {
            int nSomme = 0;
            for (int i = 1; i <= nMax; i++)
            {
                nSomme = (nSomme + i);
            }
            return nSomme;
        }

        public static void Main()
        {
            // Exemple de code WLangage - logique metier
            // Calcul d'une facture avec remise
            // Programme principal de demonstration
            nFacture = CalculerTotalHT(50.0, 3);
            Console.WriteLine("Total HT : " + nFacture);
            Console.WriteLine("Total TTC : " + CalculerTTC(nFacture));
            Console.WriteLine(FormaterClient("dupont", "Jean"));
        }
    }
}
