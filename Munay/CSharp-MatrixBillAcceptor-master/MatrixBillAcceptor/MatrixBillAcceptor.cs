using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using MatrixBillAcceptor.UsbHid;

namespace MatrixBillAcceptor
{
    public delegate void WaitingEvent(MatrixBillAcceptor sender);
    public delegate void BillAcceptingEvent(MatrixBillAcceptor sender);
    public delegate void BillEscrowedEvent(MatrixBillAcceptor sender, int billAmount);
    public delegate void BillStackingEvent(MatrixBillAcceptor sender, int billAmount);
    public delegate void BillStackedEvent(MatrixBillAcceptor sender, int billAmount);
    public delegate void BillReturningEvent(MatrixBillAcceptor sender);
    public delegate void BillReturnedEvent(MatrixBillAcceptor sender);
    public delegate void BillRejectingEvent(MatrixBillAcceptor sender);
    public delegate void BillRejectedEvent(MatrixBillAcceptor sender);

    public delegate void FailureEvent(MatrixBillAcceptor sender);
    public delegate void FailureEndedEvent(MatrixBillAcceptor sender);
    public delegate void PowerUpEvent(MatrixBillAcceptor sender);
    public delegate void PoweredUpEvent(MatrixBillAcceptor sender);
    public delegate void CashboxFullEvent(MatrixBillAcceptor sender);
    public delegate void CashboxFullEndedEvent(MatrixBillAcceptor sender);
    public delegate void CheatedEvent(MatrixBillAcceptor sender);
    public delegate void NoteJammedEvent(MatrixBillAcceptor sender);
    public delegate void NoteUnjammedEvent(MatrixBillAcceptor sender);
    public delegate void CashboxPresentEvent(MatrixBillAcceptor sender);
    public delegate void CashboxNotPresentEvent(MatrixBillAcceptor sender);

    public delegate void InvalidCommandEvent(MatrixBillAcceptor sender);

    public class MatrixBillAcceptor : Form
    {
        /// <summary>
        /// Dispatched when a bill is waiting to be read
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event WaitingEvent Waiting;

        /// <summary>
        /// Dispatched when a bill is being accepted
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event BillAcceptingEvent BillAccepting;

        /// <summary>
        /// Dispatched when a bill is in escrow
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        /// <param name="billAmount">The denomination of the bill</param>
        public event BillEscrowedEvent BillEscrowed;

        /// <summary>
        /// Dispatched when a bill is being stacked
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        /// <param name="billAmount">The denomination of the bill</param>
        public event BillStackingEvent BillStacking;

        /// <summary>
        /// Dispatched when the bill is stacked
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        /// <param name="billAmount">The denomination of the bill</param>
        public event BillStackedEvent BillStacked;

        /// <summary>
        /// Dispatched when the bill is being returned
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event BillReturningEvent BillReturning;

        /// <summary>
        /// Dispatched when the bill was returned
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event BillReturnedEvent BillReturned;

        /// <summary>
        /// Dispatched when the bill is being rejected (if it is invalid)
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event BillRejectingEvent BillRejecting;

        /// <summary>
        /// Dispatched when the bill was rejected (if it was invalid)
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event BillRejectedEvent BillRejected;

        /* Internal errors */

        /// <summary>
        /// Dispatched when the bill acceptor has an internal error
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event FailureEvent Failure;

        /// <summary>
        /// Dispatched when the bill acceptor stops having an internal error
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event FailureEndedEvent FailureEnded;

        /// <summary>
        /// Dispatched when the bill acceptor is powering up
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event PowerUpEvent PowerUp;

        /// <summary>
        /// Dispatched when the bill acceptor has fully powered up
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event PoweredUpEvent PoweredUp;

        /// <summary>
        /// Dispatched when the cashbox is full
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event CashboxFullEvent CashboxFull;

        /// <summary>
        /// Dispatched when the cashbox was emptied after being full
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event CashboxFullEndedEvent CashboxFullEnded;

        /// <summary>
        /// Dispatched when the bill acceptor detects cheating
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event CheatedEvent Cheated;

        /// <summary>
        /// Dispatched when a bill is jammed
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event NoteJammedEvent NoteJammed;

        /// <summary>
        /// Dispatched when a bill is unjammed
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event NoteUnjammedEvent NoteUnjammed;

        /// <summary>
        /// Dispatched when the bill acceptor has a cashbox re-enabled
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event CashboxPresentEvent CashboxPresent;

        /// <summary>
        /// Dispatched when the bill acceptor has a cashbox detached
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event CashboxNotPresentEvent CashboxNotPresent;

        /// <summary>
        /// Dispatched when an invalid USB command was sent to the bill acceptor
        /// </summary>
        /// <param name="sender">The acceptor which sent the event</param>
        public event InvalidCommandEvent InvalidCommand;

        private UsbHidPort usbPort = new UsbHidPort();

        /// <summary>
        /// Controls whether the bill acceptor accepts $1 bills
        /// </summary>
        public bool AcceptOnes = false;

        /// <summary>
        /// Controls whether the bill acceptor accepts $5 bills
        /// </summary>
        public bool AcceptFives = false;

        /// <summary>
        /// Controls whether the bill acceptor accepts $10 bills
        /// </summary>
        public bool AcceptTens = false;

        /// <summary>
        /// Controls whether the bill acceptor accepts $20 bills
        /// </summary>
        public bool AcceptTwenties = false;

        /// <summary>
        /// Controls whether the bill acceptor accepts $100 bills
        /// </summary>
        public bool AcceptHundreds = false;

        /// <summary>
        /// Controls whether the bill acceptor will accept any bills
        /// </summary>
        public new bool Enabled = true;

        private AcceptorDataFrame lastState = new AcceptorDataFrame(new byte[]{0x00, 0x00, 0x00, 0x00, 0x00, 0x00});
        private AcceptorDataFrame thisState = new AcceptorDataFrame(new byte[] { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 });

        public AcceptorDataFrame State
        {
            get
            {
                return thisState;
            }
        }

        public MatrixBillAcceptor()
        {
            usbPort.VendorId = 0x0ce5;
            usbPort.ProductId = 0x0003;

            usbPort.OnSpecifiedDeviceArrived += new EventHandler(usbPort_OnSpecifiedDeviceArrived);
            usbPort.OnSpecifiedDeviceRemoved += new EventHandler(usbPort_OnSpecifiedDeviceRemoved);
            usbPort.OnDeviceArrived += new EventHandler(usbPort_OnDeviceArrived);
            usbPort.OnDeviceRemoved += new EventHandler(usbPort_OnDeviceRemoved);

            usbPort.OnDataRecieved += new DataRecievedEventHandler(usbPort_OnDataRecieved);
            usbPort.OnDataSend += new EventHandler(usbPort_OnDataSend);
            
            this.Show();

            Thread t = new Thread(new ThreadStart(KeepAlive));
            t.Start();
        }

        private static void KeepAlive()
        {
            while (true)
            {
                Thread.Sleep(1000);
            }
        }

        void usbPort_OnDeviceRemoved(object sender, EventArgs e)
        {
            
        }

        void usbPort_OnDeviceArrived(object sender, EventArgs e)
        {
            
        }

        void usbPort_OnSpecifiedDeviceRemoved(object sender, EventArgs e)
        {
            
        }

        void usbPort_OnDataSend(object sender, EventArgs e)
        {
            
        }

        void usbPort_OnSpecifiedDeviceArrived(object sender, EventArgs e)
        {
            
        }

        private void send(byte[] data)
        {
            if (usbPort.SpecifiedDevice != null)
            {
                usbPort.SpecifiedDevice.SendData(data);
            }
        }

        private void sendFrame()
        {
            HostDataFrame df = new HostDataFrame();
            df.ChannelsEnabled = new bool[] { AcceptOnes, AcceptFives, AcceptTens, AcceptTwenties, AcceptHundreds };

            // Don't do anything while it's powering up.
            if (!thisState.PowerUp)
            {
                // Accept bills if they're escrowed and bill accepting is turned on.
                if (thisState.Status == StatusState.Escrowed)
                {
                    if (Enabled)
                    {
                        df.ReturnControl = false;
                        df.StackControl = true;
                    }
                    else
                    {
                        df.ReturnControl = true;
                        df.StackControl = false;
                    }
                }

                // Dispatch status change events when the status changes.
                if (thisState.Status != lastState.Status)
                {
                    switch (thisState.Status)
                    {
                        case StatusState.None:
                            if (Waiting != null)
                            {
                                Waiting(this);
                            }
                            break;
                        case StatusState.Accepting:
                            if (BillAccepting != null)
                            {
                                BillAccepting(this);
                            }
                            break;
                        case StatusState.Escrowed:
                            if (BillEscrowed != null)
                            {
                                BillEscrowed(this, thisState.Amount);
                            }
                            break;
                        case StatusState.Stacking:
                            if (BillStacking != null)
                            {
                                BillStacking(this, thisState.Amount);
                            }
                            break;
                        case StatusState.Stacked:
                            if (BillStacked != null)
                            {
                                BillStacked(this, thisState.Amount);
                            }
                            break;
                        case StatusState.Returning:
                            if (BillReturning != null)
                            {
                                BillReturning(this);
                            }
                            break;
                        case StatusState.Returned:
                            if (BillReturned != null)
                            {
                                BillReturned(this);
                            }
                            break;
                        case StatusState.Rejecting:
                            if (BillRejecting != null)
                            {
                                BillRejecting(this);
                            }
                            break;
                        case StatusState.Rejected:
                            if (BillRejected != null)
                            {
                                BillRejected(this);
                            }
                            break;
                    }
                }

                // Dispatch event events:
                if (thisState.Failure && !lastState.Failure && Failure != null)
                {
                    Failure(this);
                }else if (!thisState.Failure && lastState.Failure && FailureEnded != null)
                {
                    FailureEnded(this);
                }

                if (!thisState.PowerUp && lastState.PowerUp && PoweredUp != null)
                {
                    PoweredUp(this);
                }

                if (thisState.CashboxFull && !lastState.CashboxFull && CashboxFull != null)
                {
                    CashboxFull(this);
                }
                else if (!thisState.CashboxFull && lastState.CashboxFull && CashboxFullEnded != null)
                {
                    CashboxFullEnded(this);
                }

                if (thisState.Cheated && !lastState.Cheated && Cheated != null)
                {
                    Cheated(this);
                }

                if (thisState.NoteJammed && !lastState.NoteJammed && NoteJammed != null)
                {
                    NoteJammed(this);
                }
                else if (!thisState.NoteJammed && lastState.NoteJammed && NoteUnjammed != null)
                {
                    NoteUnjammed(this);
                }

                if (thisState.CashboxPresent && !lastState.CashboxPresent && CashboxPresent != null)
                {
                    CashboxPresent(this);
                }
                else if (!thisState.CashboxPresent && lastState.CashboxPresent && CashboxNotPresent != null)
                {
                    CashboxNotPresent(this);
                }

                if (thisState.InvalidCommand && !lastState.InvalidCommand && InvalidCommand != null)
                {
                    InvalidCommand(this);
                }
            }
            else
            {
                if (!lastState.PowerUp && PowerUp != null)
                {
                    PowerUp(this);
                }
            }

            // Increment the sequence number, or reset it to 0 if it's FFh.
            unchecked
            {
                df.sequenceNumber = (byte)(thisState.SequenceNumber + 1);
            }

            send(df);
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            this.Visible = false;
        }

        void usbPort_OnDataRecieved(object sender, DataRecievedEventArgs args)
        {
            lastState = thisState;
            thisState = new AcceptorDataFrame(args.data);

            Thread.Sleep(25);
            sendFrame();
        }

        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            usbPort.RegisterHandle(Handle);
        }

        protected override void WndProc(ref Message m)
        {
            usbPort.ParseMessages(ref m);
            base.WndProc(ref m);
        }

        private void InitializeComponent()
        {
            usbPort.CheckDevicePresent();
        }
    }
}
