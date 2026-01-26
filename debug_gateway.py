
import sys
import os
import polars as pl

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from kaggle_evaluation import aimo_3_gateway
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def debug():
    print("Initializing Gateway...")
    # We need to provide a path to test.csv because the default path /kaggle/input/... doesn't exist
    gateway = aimo_3_gateway.AIMO3Gateway(data_paths=('test.csv',))
    gateway.unpack_data_paths()
    
    print("Generating batches...")
    gen = gateway.generate_data_batches()
    
    try:
        first_batch = next(gen)
        data_batch, row_ids = first_batch
        
        print(f"Type of data_batch: {type(data_batch)}")
        print(f"Content of data_batch: {data_batch}")
        
        if isinstance(data_batch, pl.DataFrame):
            print("Iterating data_batch (simulating *unpacking):")
            for item in data_batch:
                print(f"  Item: {item}")
                
    except StopIteration:
        print("No data generated.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug()
