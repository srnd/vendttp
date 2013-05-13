using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace MatrixBillAcceptor
{
    public enum StatusState
    {
        None = 0,
        Accepting = 1,
        Escrowed = 2,
        Stacking = 4,
        Stacked = 8,
        Returning = 16,
        Returned = 32,
        Rejecting = 64,
        Rejected = 128
    }

    public class AcceptorDataFrame
    {
        public StatusState Status;
        public bool Failure;
        public bool PowerUp;
        public bool CashboxFull;
        public bool Cheated;
        public bool NoteJammed;
        public bool CashboxPresent;
        public bool InvalidCommand;

        public int Amount;

        public byte SequenceNumber;

        public AcceptorDataFrame(byte[] bits)
        {
            byte status = bits[1];
            try
            {
                Status = (StatusState)((int)status);
            }
            catch
            {
                Status = StatusState.Rejected;
            }

            byte e = bits[2];
            Failure = (e & 1) > 0;
            PowerUp = (e & 2) > 0;
            CashboxFull = (e & 4) > 0;
            Cheated = (e & 8) > 0;
            NoteJammed = (e & 16) > 0;
            CashboxPresent = (e & 32) > 0;
            InvalidCommand = (e & 64) > 0;

            switch ((int)bits[4])
            {
                case 1:
                    Amount = 1;
                    break;
                case 2:
                    Amount = 5;
                    break;
                case 3:
                    Amount = 10;
                    break;
                case 4:
                    Amount = 20;
                    break;
                case 5:
                    Amount = 100;
                    break;
                default:
                    Amount = 0;
                    break;
            }

            SequenceNumber = bits[5];
        }
    }
}
