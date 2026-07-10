import "dotenv/config";
import { pipeline } from "./pipeline.js";

const CO_CONT_LIST = process.env.CO_CONT_LIST
  ? process.env.CO_CONT_LIST.split(",").map((s) => s.trim())
  : [];

export async function migrate_conts(db, docs) {
  const promises = CO_CONT_LIST.map(async (co_cont) => {
    let pipeline_migrate = [
      { $documents: docs },
      ...pipeline.newsid2contid,
      ...pipeline.migrate_cont,
    ];

    pipeline_migrate.at(-3)["$lookup"].from = co_cont;
    return await db
      .aggregate(pipeline_migrate, { allowDiskUse: true })
      .toArray();
  });
  await Promise.all(promises);
}
