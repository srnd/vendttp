CSharp-MatrixBillAcceptor
=========================

A C# library for interfacing with a USB Matrix Bill Acceptor.

Usage
=====

Getting Started
---------------

Add the project as a reference, then just bind to a bill acceptor with the following:

    MatrixBillAcceptor acceptor = new BillAcceptor();

Configuring
-----------

Configure what bills the acceptor will accept like so:

    acceptor.AcceptOnes = true; // $1s are okay!
    acceptor.AcceptFives = true; // $5s are okay!
    acceptor.AcceptTens = true; // $10s are okay!
    acceptor.AcceptTwenties = true; // $20s are okay!
    acceptor.AcceptHundreds = false; // No $100s!

You can enable or disable the acceptor as a whole with:

    acceptor.Enabled = false;

Handling Events
---------------

The bill acceptor has a lot of events you can recieve. Usually, you'll only care about the `BillStacked` event:

    private static void Main(string[] args)
    {
        // [...] (see previous sections)

        acceptor.BillStacked += new BillStackedEvent(acceptor_BillStacked);
    }
       
    static int amount = 0;
    static void acceptor_BillStacked(BillAcceptor sender, int billAmount)
    {
        amount += billAmount; 
        Console.WriteLine("You have $" + amount + ".00 in credit!");
    }

Consult the Intellisense documentation for the other events.
