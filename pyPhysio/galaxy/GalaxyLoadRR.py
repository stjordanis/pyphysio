from pyPhysio.galaxy.ParamExecClass import ParamExecClass

__author__ = 'AleB'

from pyPhysio.Files import load_ibi_from_ecg, load_ibi_from_bvp, load_ds_from_csv_column, save_ds_to_csv


class GalaxyLoadRR(ParamExecClass):
    """
    FILE_CSV -> T_RR_CSV
    kwargs['input'] ----> input file
    kwargs['output'] ---> output file
    kwargs['data_type'] ---> [ 'ecg', 'bvp', 'rr' ]
    """

    def execute(self):
        inp = self._kwargs['input']
        out = self._kwargs['output']
        d = self._kwargs['data_type']
        if d == 'ecg':
            ds = load_ibi_from_ecg(inp)
        elif d == 'bvp':
            ds = load_ibi_from_bvp(inp)
        elif d == 'rr':
            ds = load_ds_from_csv_column(inp)
        else:
            raise ValueError("data_type is " + d)
        save_ds_to_csv(ds, out)